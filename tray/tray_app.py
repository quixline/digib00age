"""
ComicVault Tray App — launches the reader server and sits in the system tray.

Run from the project root:
    python tray\\tray_app.py        (console visible, for debugging)
    pythonw tray\\tray_app.py       (silent, for normal/startup use)

Tray icon (left or right click) shows a menu with:
    - Open Library                  (opens in an app-mode window, see open_app_window())
    - Admin                         (same)
    - Metadata Editor               (same; opens the URL only — does not launch/manage that process)
    - Start ComicVault at login     (checkable — creates/removes the Windows Startup shortcut)
    - Stop Server                   (stops the reader subprocess only; tray keeps running)
    - Start Server                  (restarts it; no-op if already running)
    - Close                         (stops the reader, then exits the tray app)

Reader status (starting/running/stopped) is shown via the tray icon's
coloured dot (yellow/green/red), not via the menu text — see build_menu()
for why the menu label is intentionally static.

A background thread checks the reader server every 30 seconds and restarts
it if the process has died — unless it was stopped deliberately via "Stop
Server"/"Close" (see `manually_stopped`).
"""

import ctypes
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser

from PIL import Image, ImageDraw
import pystray

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import READER_PORT  # noqa: E402

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray.log")
HEALTH_CHECK_INTERVAL = 30  # seconds
STARTUP_WAIT_TIMEOUT = 15  # seconds to wait for the port to open after launch

STARTUP_SHORTCUT_PATH = os.path.join(
    os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "ComicVault.lnk"
)
START_BAT_PATH = os.path.join(PROJECT_ROOT, "start.bat")

state_lock = threading.Lock()
reader_process = None
reader_status = "starting"  # "starting" | "running" | "stopped"
manually_stopped = False    # True after "Stop Server"/"Close" — suppresses health-check auto-restart
stop_event = threading.Event()


def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass


def port_is_open(port, timeout=1.0):
    try:
        with socket.create_connection(("localhost", port), timeout=timeout):
            return True
    except OSError:
        return False


READER_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reader_stdout.log")

# App-mode launch: Edge/Chrome's --app=<url> opens a chromeless window (no
# tabs/address bar) instead of a tab in the user's regular browser session.
# Edge preferred (Windows default, virtually always present); Chrome as
# fallback; plain webbrowser.open() (a normal tab) if neither is found.
_APP_BROWSER_CANDIDATES = [
    os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Microsoft", "Edge", "Application", "msedge.exe"),
    os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Microsoft", "Edge", "Application", "msedge.exe"),
    os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
]
_app_browser_exe = None  # resolved lazily; False once probed with nothing found


def _find_app_browser_exe():
    global _app_browser_exe
    if _app_browser_exe is None:
        _app_browser_exe = next((p for p in _APP_BROWSER_CANDIDATES if os.path.exists(p)), False)
        if _app_browser_exe:
            log(f"App-mode browser: {_app_browser_exe}")
        else:
            log("App-mode browser: none found (Edge/Chrome), falling back to webbrowser.open().")
    return _app_browser_exe


def open_app_window(url):
    """Opens `url` in a chromeless app-mode window rather than a browser tab."""
    exe = _find_app_browser_exe()
    if exe:
        try:
            subprocess.Popen(
                [exe, f"--app={url}"],
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            return
        except OSError as e:
            log(f"App-mode launch failed ({e}), falling back to webbrowser.open().")
    webbrowser.open(url)

# digib00age brand mark (frontend/images/favicon.png) — reused here as the
# tray icon's base glyph. Square with a transparent background, unlike
# icon-oo.png/logo1.png (166x100 horizontal logotype), which don't fit a
# square tray icon. Visual only: the tray app's process/menu name stays
# "ComicVault" (SPEC.md Section 1's 2026-07-07 scope note still holds for
# everything except this glyph).
FAVICON_PATH = os.path.join(PROJECT_ROOT, "frontend", "images", "favicon.png")
_base_icon_cache = None


def start_reader():
    global reader_process
    log("Starting reader server subprocess...")
    # When this app runs under pythonw (no console), sys.stdout/stderr are None
    # in a child that inherits the same console-less state, which crashes any
    # print() call in start_server.py. Redirect to a file so the child always
    # has real stream objects.
    reader_log = open(READER_LOG_PATH, "a", encoding="utf-8")
    reader_process = subprocess.Popen(
        [sys.executable, "start_server.py"],
        cwd=PROJECT_ROOT,
        stdout=reader_log,
        stderr=reader_log,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )


def wait_for_startup():
    global reader_status
    deadline = time.time() + STARTUP_WAIT_TIMEOUT
    while time.time() < deadline:
        if port_is_open(READER_PORT):
            with state_lock:
                reader_status = "running"
            log("Reader server is up.")
            return
        time.sleep(1)
    log("Reader server did not come up within the startup timeout.")


def health_check_loop():
    global reader_status
    while not stop_event.wait(HEALTH_CHECK_INTERVAL):
        with state_lock:
            proc = reader_process
            stopped_deliberately = manually_stopped
        if proc is None:
            continue
        if proc.poll() is not None:
            if stopped_deliberately:
                # Don't fight a deliberate "Stop Server"/"Close" by auto-restarting.
                continue
            log(f"Reader process exited (code {proc.returncode}). Restarting.")
            with state_lock:
                reader_status = "starting"
            start_reader()
            wait_for_startup()
        else:
            with state_lock:
                reader_status = "running" if port_is_open(READER_PORT) else "stopped"


def _load_base_icon(size):
    """digib00age favicon, letterboxed onto a transparent size x size canvas."""
    base = Image.open(FAVICON_PATH).convert("RGBA")
    base.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - base.width) // 2, (size - base.height) // 2)
    canvas.paste(base, offset, base)
    return canvas


def make_icon_image(status):
    global _base_icon_cache

    color_map = {
        "running": (66, 200, 110),
        "starting": (230, 180, 50),
        "stopped": (220, 70, 70),
    }
    dot_color = color_map.get(status, (150, 150, 150))

    size = 64
    if _base_icon_cache is None:
        _base_icon_cache = _load_base_icon(size)
    image = _base_icon_cache.copy()
    draw = ImageDraw.Draw(image)

    # Status dot, bottom-right (unchanged position/colours from the previous
    # book-glyph icon)
    draw.ellipse([40, 40, 60, 60], fill=dot_color, outline=(20, 20, 20, 255))

    return image


def open_library(icon=None, item=None):
    open_app_window(f"http://localhost:{READER_PORT}")


def open_admin(icon=None, item=None):
    open_app_window(f"http://localhost:{READER_PORT}/admin")


def open_editor(icon=None, item=None):
    # Editor is part of the same FastAPI app, no separate process/port
    # (EDITOR_SPEC.md Section 2) — was http://localhost:{EDITOR_PORT} (8001).
    open_app_window(f"http://localhost:{READER_PORT}/editor")


def _terminate_reader_process():
    """Shared terminate/grace-period/kill logic for Stop Server and Close."""
    with state_lock:
        proc = reader_process
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def stop_server(icon=None, item=None):
    """Stops the reader subprocess only. The tray app keeps running."""
    global manually_stopped, reader_status
    log("Stop Server requested from tray menu.")
    with state_lock:
        manually_stopped = True
        reader_status = "stopped"
    _terminate_reader_process()


def start_server(icon=None, item=None):
    """Restarts the reader subprocess. No-op if it's already running."""
    global manually_stopped, reader_status
    log("Start Server requested from tray menu.")
    with state_lock:
        proc = reader_process
        if proc is not None and proc.poll() is None:
            log("Start Server: reader is already running, ignoring.")
            return
        manually_stopped = False
        reader_status = "starting"
    start_reader()
    threading.Thread(target=wait_for_startup, daemon=True).start()


def close_app(icon, item=None):
    """Stops the reader subprocess, then exits the tray app entirely."""
    global manually_stopped
    log("Close requested from tray menu.")
    stop_event.set()
    with state_lock:
        manually_stopped = True
    _terminate_reader_process()
    icon.stop()


def is_autostart_enabled(item=None):
    return os.path.exists(STARTUP_SHORTCUT_PATH)


def toggle_autostart(icon=None, item=None):
    """Creates or removes the Windows Startup shortcut. The shortcut's own
    existence is the source of truth for the menu checkbox — no config.json
    flag to keep in sync."""
    if os.path.exists(STARTUP_SHORTCUT_PATH):
        try:
            os.remove(STARTUP_SHORTCUT_PATH)
            log("Autostart disabled (shortcut removed).")
        except OSError as e:
            log(f"Failed to remove autostart shortcut: {e}")
    else:
        try:
            import win32com.client  # imported lazily: a missing pywin32 shouldn't crash tray startup
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(STARTUP_SHORTCUT_PATH)
            shortcut.TargetPath = START_BAT_PATH
            shortcut.WorkingDirectory = PROJECT_ROOT
            shortcut.WindowStyle = 7  # minimized
            shortcut.save()
            log("Autostart enabled (shortcut created).")
        except Exception as e:
            log(f"Failed to create autostart shortcut: {e}")


def build_menu():
    # Status is conveyed only via the tray icon's coloured dot (see
    # make_icon_image / update_icon_loop), not via a live-updating menu label.
    #
    # pystray wraps every menu item callback in a try/finally that calls
    # icon.update_menu() (pystray/_base.py _handler) — this has always fired
    # after every click on every item, including the original Open Library/
    # Admin/Editor items, with no issue, because it runs on the message-pump
    # thread strictly after the native TrackPopupMenuEx popup has already
    # closed (it's a blocking call) — there's no menu open to corrupt at that
    # point. The bug fixed 2026-06-17 (a click on "Admin" firing "Open
    # Library") came specifically from a *periodic background thread*
    # calling icon.update_menu() on a timer, which could race with the menu
    # being open concurrently. The real rule is: never call update_menu()
    # from a background thread (update_icon_loop, health_check_loop) — not
    # "never call it at all." This is why "Start ComicVault at login" below
    # can safely be a checkable item: its checkmark updates correctly on the
    # very next click with no extra code, since pystray already rebuilds the
    # menu after every click via the mechanism above.
    return pystray.Menu(
        pystray.MenuItem("ComicVault", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Library", open_library),
        pystray.MenuItem("Admin", open_admin),
        pystray.MenuItem("Metadata Editor", open_editor),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start ComicVault at login", toggle_autostart, checked=is_autostart_enabled),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Stop Server", stop_server),
        pystray.MenuItem("Start Server", start_server),
        pystray.MenuItem("Close", close_app),
    )


def update_icon_loop(icon):
    last_status = None
    while not stop_event.wait(2):
        with state_lock:
            status = reader_status
        if status != last_status:
            icon.icon = make_icon_image(status)
            last_status = status


def _enable_dark_menu_support():
    """
    Makes the native popup menu follow Windows' own "Apps use dark mode"
    setting, via the undocumented SetPreferredAppMode export (ordinal 135,
    no public name) in uxtheme.dll. Must run before any window/menu HWND is
    created. This cannot force a dark menu on a system set to light mode —
    it only stops the app being forced light when the OS itself is dark.
    """
    try:
        uxtheme = ctypes.WinDLL("uxtheme.dll")
        set_preferred_app_mode = uxtheme[135]
        set_preferred_app_mode.argtypes = [ctypes.c_int]
        set_preferred_app_mode(1)  # 1 = AllowDark
    except Exception as e:
        log(f"Dark menu mode not applied (non-fatal): {e}")


def main():
    _enable_dark_menu_support()

    log("=" * 40)
    log("ComicVault tray app starting.")

    start_reader()
    health_thread = threading.Thread(target=health_check_loop, daemon=True)
    health_thread.start()

    icon = pystray.Icon(
        "ComicVault",
        make_icon_image("starting"),
        "ComicVault",
        menu=build_menu(),
    )

    icon_thread = threading.Thread(target=update_icon_loop, args=(icon,), daemon=True)
    icon_thread.start()

    threading.Thread(target=wait_for_startup, daemon=True).start()

    icon.run()
    log("Tray icon stopped. Exiting.")


if __name__ == "__main__":
    main()
