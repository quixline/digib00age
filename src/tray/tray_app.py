"""
digib00age Tray App — launches the reader server and sits in the system tray.

Run from the repo root:
    python src\\tray\\tray_app.py        (Windows, console visible, for debugging)
    pythonw src\\tray\\tray_app.py       (Windows, silent, for normal/startup use)
    python3 src/tray/tray_app.py         (Linux)

Tray icon (left or right click) shows a menu with:
    - Open Library                  (opens in an app-mode window, see open_app_window())
    - Admin                         (same)
    - Metadata Editor               (same; opens the URL only — does not launch/manage that process)
    - Start digib00age at login     (checkable — creates/removes the OS-appropriate autostart
                                      entry: a Windows Startup-folder shortcut, or a Linux
                                      ~/.config/autostart/ .desktop file)
    - Stop Server                   (stops the reader subprocess only; tray keeps running)
    - Start Server                  (restarts it; no-op if already running)
    - Close                         (stops the reader, then exits the tray app)

Reader status (starting/running/stopped) is shown via the tray icon's
coloured dot (yellow/green/red), not via the menu text — see build_menu()
for why the menu label is intentionally static.

A background thread checks the reader server every 30 seconds and restarts
it if the process has died — unless it was stopped deliberately via "Stop
Server"/"Close" (see `manually_stopped`).

A local-only control server (127.0.0.1:TRAY_CONTROL_PORT, see
start_control_server()) also runs alongside the reader subprocess so the web
UI's "Read"/cover-click action can ask the tray to open the browser-popout
reader (frontend/reader.html/js) as its own chromeless --app= window,
matching Open Library/Admin/Metadata Editor above — added 2026-07-29 to
replace the old Windows Flutter reader's comicvault:// deep link.
"""

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from urllib.parse import urlparse, parse_qs

IS_WINDOWS = sys.platform == "win32"

if getattr(sys, "frozen", False) and not IS_WINDOWS:
    # PyGObject/AppIndicator is deliberately not frozen into this binary (see
    # DECISIONS.md "Linux .deb release" + BUG-040) — GObject-Introspection's
    # typelib machinery is fragile to bundle, and the system already has a
    # correctly-built python3-gi (a .deb Depends:). Point at it here, before
    # pystray's own lazy `import gi` runs, same as the dev venv's
    # --system-site-packages achieves for an unfrozen run.
    sys.path.append("/usr/lib/python3/dist-packages")

from PIL import Image, ImageDraw
import pystray

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    import winreg

if getattr(sys, "frozen", False):
    if IS_WINDOWS:
        # A frozen Windows build (PyInstaller MSI install) has no src/
        # nesting — backend/frontend/config.json sit flat next to this exe —
        # and __file__ isn't a real on-disk path once bundled, so base
        # everything on sys.executable's directory instead. Mirrors the same
        # branch in backend/config.py. Already verified working live against
        # a real %LocalAppData% install.
        PROJECT_ROOT = os.path.dirname(sys.executable)
    else:
        # This file is the PyInstaller entry script, not a regularly-imported
        # package module — its __file__ isn't reliably meaningful once frozen
        # (unlike backend/config.py's, which PyInstaller preserves for real
        # package members). sys._MEIPASS is PyInstaller's own documented,
        # version-independent pointer to the bundle's data directory (the
        # --onedir dist folder), used here to still find the bundled
        # frontend/images/favicon.png below.
        PROJECT_ROOT = sys._MEIPASS
    REPO_ROOT = PROJECT_ROOT
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/
    sys.path.insert(0, PROJECT_ROOT)
    # start.bat/start_server.py live at the true repo root, one level above src/
    # (tray_app.py itself is launched from there, but backend/frontend moved
    # into src/ so PROJECT_ROOT above no longer is the repo root).
    REPO_ROOT = os.path.dirname(PROJECT_ROOT)

from backend.config import READER_PORT  # noqa: E402

if getattr(sys, "frozen", False) and not IS_WINDOWS:
    # A .deb install lands in /opt, which isn't user-writable — writing
    # tray.log/reader_stdout.log next to the binary (the dev/Windows-per-user
    # default below) crashed the app outright on first real install/launch
    # test (unguarded open() in start_reader() -> PermissionError). Reuse the
    # same XDG data dir config.py already redirects db/thumbnails to when
    # frozen on Linux, so logs land somewhere actually writable.
    from backend.config import _xdg_data_dir
    _LOG_DIR = str(_xdg_data_dir())
    os.makedirs(_LOG_DIR, exist_ok=True)
elif getattr(sys, "frozen", False):
    # Frozen Windows: PROJECT_ROOT is the per-user install dir, already
    # writable — no XDG-style redirect needed there.
    _LOG_DIR = PROJECT_ROOT
else:
    _LOG_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_PATH = os.path.join(_LOG_DIR, "tray.log")
HEALTH_CHECK_INTERVAL = 30  # seconds
STARTUP_WAIT_TIMEOUT = 15  # seconds to wait for the port to open after launch

# Local-only control port the web UI calls to ask the tray to open the
# browser-popout reader (frontend/reader.html/js) as its own chromeless
# --app= window, same as Open Library/Admin/Metadata Editor below — added
# 2026-07-29 when a plain window.open() popup was found to still show an
# address bar (window.open can't suppress it; only an --app=-launched
# window can). Bound to 127.0.0.1 only, never the LAN.
TRAY_CONTROL_PORT = 9801

if IS_WINDOWS:
    STARTUP_SHORTCUT_PATH = os.path.join(
        os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "digib00age.lnk"
    )
    # Pre-rebrand shortcut filename (2026-07-28 rebrand, DECISIONS.md). Still a
    # valid, functioning Startup entry on any machine that enabled autostart
    # before this change — Windows runs it by presence in the Startup folder,
    # not by name. Left in place it would keep launching a second tray instance
    # once the new-named shortcut is created via a toggle, since
    # is_autostart_enabled() only checks the new path. Cleaned up once at
    # startup (see _migrate_legacy_startup_shortcut()) rather than requiring
    # Tez to manually re-toggle autostart after updating.
    LEGACY_STARTUP_SHORTCUT_PATH = os.path.join(
        os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "ComicVault.lnk"
    )
else:
    # Linux equivalent of the Windows Startup folder — the freedesktop.org
    # Desktop Entry autostart location every major desktop environment
    # (GNOME, Cinnamon, KDE, ...) reads on login.
    AUTOSTART_DESKTOP_PATH = os.path.join(
        os.path.expanduser("~"), ".config", "autostart", "digib00age.desktop"
    )
START_BAT_PATH = os.path.join(REPO_ROOT, "start.bat")

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


READER_LOG_PATH = os.path.join(_LOG_DIR, "reader_stdout.log")

# App-mode launch: Chrome/Edge-family browsers' --app=<url> opens a
# chromeless window (no tabs/address bar) instead of a tab in the user's
# regular browser session. The real default browser is resolved via the
# registry on Windows / xdg-settings on Linux (see
# _resolve_default_browser_exe()) whenever possible; this hardcoded list is
# only the fallback for when that lookup fails (unreadable, default is a
# non-Chromium browser, etc.) — Edge first on Windows since it's virtually
# always present; on Linux these are bare command names resolved via PATH
# (see _find_app_browser_exe()) rather than absolute paths, since Linux
# package installs don't share Windows' Program Files convention.
if IS_WINDOWS:
    _APP_BROWSER_CANDIDATES = [
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
    ]
else:
    _APP_BROWSER_CANDIDATES = [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "brave-browser", "microsoft-edge", "microsoft-edge-stable",
    ]
_app_browser_exe = None  # resolved lazily; False once probed with nothing found

# Chromium-family browsers all support the --app=<url> chromeless-window
# flag; anything else (e.g. Firefox) doesn't, so a resolved default outside
# this set is treated as "no opinion" and falls through to the hardcoded list.
_CHROMIUM_APP_MODE_EXES = {
    "msedge.exe", "chrome.exe", "brave.exe", "vivaldi.exe", "opera.exe", "chromium.exe",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "brave-browser", "microsoft-edge", "microsoft-edge-stable", "vivaldi-stable", "opera",
}


def _resolve_default_browser_exe_windows():
    """Resolve the real executable Windows launches for https:// links —
    i.e. the user's actual registered default browser — instead of guessing
    install paths. `HKCU\\...\\UrlAssociations\\https\\UserChoice`'s ProgId
    value (e.g. "BraveHTML", "ChromeHTML", "MSEdgeHTML") is what Windows'
    own "Choose default apps" UI writes; HKEY_CLASSES_ROOT is Windows' own
    merged view of HKCU/HKLM Software\\Classes, so one lookup resolves that
    ProgId's real command regardless of whether the browser is installed
    per-user (e.g. Chrome/Brave under %LOCALAPPDATA%) or machine-wide.
    Returns the exe path only if it's a Chromium-family browser (supports
    --app=) and the path exists; returns None otherwise so the caller can
    fall back to the hardcoded candidate list."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        ) as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")
    except OSError:
        return None

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{prog_id}\shell\open\command") as key:
            command, _ = winreg.QueryValueEx(key, None)
    except OSError:
        return None

    command = command.strip()
    if command.startswith('"'):
        exe_path = command[1:].split('"', 1)[0]
    else:
        exe_path = command.split(" ", 1)[0]

    if os.path.basename(exe_path).lower() not in _CHROMIUM_APP_MODE_EXES:
        return None
    if not os.path.exists(exe_path):
        return None
    return exe_path


# xdg-settings reports the default browser as a .desktop file id (e.g.
# "google-chrome.desktop") — maps the ones we recognize to their command
# name for shutil.which() resolution. Firefox (org.mozilla.firefox.desktop
# or firefox.desktop) is deliberately not mapped: it doesn't support
# --app= chromeless windows, same as any non-Chromium browser on Windows —
# an unmapped id just falls through to the candidate list below.
_DEFAULT_BROWSER_DESKTOP_ID_TO_EXE = {
    "google-chrome.desktop": "google-chrome",
    "google-chrome-stable.desktop": "google-chrome-stable",
    "chromium.desktop": "chromium",
    "chromium-browser.desktop": "chromium-browser",
    "brave-browser.desktop": "brave-browser",
    "microsoft-edge.desktop": "microsoft-edge",
}


def _resolve_default_browser_exe_linux():
    """Resolve the user's default browser via `xdg-settings`, the Linux
    equivalent of the Windows registry lookup above. Returns an exe path
    only if it's a Chromium-family browser (supports --app=) and it's
    actually on PATH; returns None otherwise (covers Firefox and any
    xdg-settings failure) so the caller falls back to the hardcoded
    candidate list."""
    try:
        result = subprocess.run(
            ["xdg-settings", "get", "default-web-browser"],
            capture_output=True, text=True, timeout=2,
        )
        desktop_id = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    exe_name = _DEFAULT_BROWSER_DESKTOP_ID_TO_EXE.get(desktop_id)
    if not exe_name:
        return None
    return shutil.which(exe_name)


def _resolve_default_browser_exe():
    return _resolve_default_browser_exe_windows() if IS_WINDOWS else _resolve_default_browser_exe_linux()


def _find_app_browser_exe():
    global _app_browser_exe
    if _app_browser_exe is None:
        default_exe = _resolve_default_browser_exe()
        if default_exe:
            _app_browser_exe = default_exe
            log(f"App-mode browser: {_app_browser_exe} (system default)")
            return _app_browser_exe

        # shutil.which() resolves both Linux's bare command names and
        # Windows' existing absolute paths correctly (an absolute path is
        # checked directly, not searched for on PATH).
        _app_browser_exe = next(
            (resolved for p in _APP_BROWSER_CANDIDATES if (resolved := shutil.which(p))), False
        )
        if _app_browser_exe:
            log(f"App-mode browser: {_app_browser_exe} (default-browser lookup failed, using fallback list)")
        else:
            log("App-mode browser: none found (default-browser lookup + fallback list), falling back to webbrowser.open().")
    return _app_browser_exe


def _get_work_area():
    """Primary display's work area (excludes the taskbar), via SPI_GETWORKAREA."""
    rect = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def _get_window_chrome_size():
    """Non-client size (title bar + resize borders) Windows adds around a
    standard resizable app window's content area, via GetSystemMetrics — so
    the reader window can be sized so its *content* area (not the outer
    frame SetWindowPos actually controls) matches the comic page, the same
    correction the old Flutter resize service made by comparing
    windowManager.getSize() against MediaQuery.sizeOf(context)."""
    gsm = ctypes.windll.user32.GetSystemMetrics
    SM_CXSIZEFRAME, SM_CYSIZEFRAME, SM_CXPADDEDBORDER, SM_CYCAPTION = 32, 33, 92, 4
    frame_x = gsm(SM_CXSIZEFRAME) + gsm(SM_CXPADDEDBORDER)
    frame_y = gsm(SM_CYSIZEFRAME) + gsm(SM_CXPADDEDBORDER)
    return frame_x * 2, frame_y * 2 + gsm(SM_CYCAPTION)


def _compute_reader_window_geometry(issue_id, timeout=15):
    """Ports the old Flutter reader's window-shape behaviour (deleted
    2026-07-29 with window_resize_service.dart, never replaced when the
    reader moved to a browser popout): size the window's content area to
    100% of the comic's actual page-1 pixel dimensions, capped to fit the
    display's work area (preserving aspect ratio) if that's too big,
    centered. Reads the full-resolution page (not /api/cover's downscaled
    thumbnail — Tez found the thumbnail-based 75% version visibly smaller
    than the cover on the issue page, 2026-07-30) since "100% of the page"
    has to mean actual page pixels. `timeout` defaults generously (some
    archives sit on slow/networked storage — a cold first-page extraction
    can take several seconds) since this always runs off the HTTP response
    path; see _activate_and_resize_new_window. Best-effort: any failure
    (page fetch, bad image, etc.) returns None and the caller applies no
    resize rather than blocking the reader from opening.
    """
    if not IS_WINDOWS:
        # win32 work-area/window-chrome APIs used below don't exist here —
        # the app-mode window still opens fine, just unsized (no-op for
        # v1, see DECISIONS.md "Linux .deb release"). Short-circuits before
        # the page-1 image fetch rather than letting it run and get thrown
        # away by the except below.
        return None
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{READER_PORT}/api/page/{issue_id}/0", timeout=timeout
        ) as resp:
            data = resp.read()
        page_w, page_h = Image.open(BytesIO(data)).size
        if page_w <= 0 or page_h <= 0:
            return None

        area_left, area_top, area_w, area_h = _get_work_area()
        chrome_w, chrome_h = _get_window_chrome_size()
        max_content_w = max(area_w - chrome_w, 1)
        max_content_h = max(area_h - chrome_h, 1)

        width, height = page_w, page_h
        if width > max_content_w or height > max_content_h:
            scale = min(max_content_w / width, max_content_h / height)
            width *= scale
            height *= scale

        frame_width = int(width) + chrome_w
        frame_height = int(height) + chrome_h
        x = area_left + (area_w - frame_width) // 2
        y = area_top + (area_h - frame_height) // 2
        return frame_width, frame_height, x, y
    except Exception as e:
        log(f"Reader window geometry skipped ({e}).")
        return None


def _resolve_process_image_basename(pid):
    """Lowercased exe basename for a PID (e.g. 'msedge.exe'), or None."""
    try:
        import win32api
        import win32con
        import win32process
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        try:
            return os.path.basename(win32process.GetModuleFileNameEx(handle, 0)).lower()
        finally:
            win32api.CloseHandle(handle)
    except Exception:
        return None


def _snapshot_top_level_hwnds(target_name):
    """Visible, titled, top-level window handles currently owned by any
    process named `target_name` (e.g. 'msedge.exe')."""
    try:
        import win32gui
        import win32process
    except ImportError:
        return set()
    hwnds = set()

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if _resolve_process_image_basename(pid) == target_name:
                hwnds.add(hwnd)
        return True

    win32gui.EnumWindows(_cb, None)
    return hwnds


def _find_new_window(before_hwnds, target_name, timeout=4.0, poll_interval=0.1):
    """Diffs against `before_hwnds` (a snapshot taken right before Popen) to
    find the browser window this launch just created. Matching "whichever
    browser window is foreground" isn't enough once more than one reader
    window is open (one per issue — Edge doesn't reuse a single app-mode
    window across different --app= URLs the way Library/Admin/Editor's
    shared, unchanging URLs let it appear to; confirmed live 2026-07-30)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        fresh = _snapshot_top_level_hwnds(target_name) - before_hwnds
        if fresh:
            return next(iter(fresh))
        time.sleep(poll_interval)
    return None


def _force_foreground(hwnd, timeout=1.5, poll_interval=0.1):
    """Repeatedly forces `hwnd` to the foreground for `timeout` seconds.
    Reapplying rather than a single call is needed because a single
    SetForegroundWindow can land mid-init and get silently overwritten a
    beat later by Chromium's own restore-last-placement/activation logic
    (confirmed live 2026-07-29). The AttachThreadInput trick is needed
    because Windows denies SetForegroundWindow to a thread that isn't
    itself foreground and hasn't just received user input — the reader
    launch arrives via a background HTTP request to the control server
    (triggered by a fetch() from whichever browser tab currently has
    focus), not direct user input to this tray process, so without it the
    new window opens behind whatever's already focused (open_app_window's
    AllowSetForegroundWindow(-1) call also targets this, but wasn't
    reliable enough alone in testing)."""
    import win32api
    import win32con
    import win32gui
    import win32process
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fg_hwnd = win32gui.GetForegroundWindow()
            fg_thread = win32process.GetWindowThreadProcessId(fg_hwnd)[0] if fg_hwnd else 0
            cur_thread = win32api.GetCurrentThreadId()
            attached = fg_thread and fg_thread != cur_thread
            if attached:
                win32process.AttachThreadInput(cur_thread, fg_thread, True)
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
            finally:
                if attached:
                    win32process.AttachThreadInput(cur_thread, fg_thread, False)
        except Exception:
            pass
        time.sleep(poll_interval)


def _activate_and_resize_new_window(before_hwnds, browser_exe, issue_id):
    """Finds the browser window this launch just created, forces it to the
    foreground, then (separately, since it can take much longer — reading
    the full page-1 image off disk/archive to get its true pixel size, on
    potentially slow/networked storage — confirmed live 2026-07-30 to
    occasionally exceed several seconds) sizes it to that issue's page-1
    dimensions once that resolves. Runs in its own thread — never blocks
    the caller (the reader control server's HTTP response needs to return
    well within the web UI's 400ms fetch timeout, see launchReader() in
    app.js, or its fallback window.open() popup fires too and a second
    window appears alongside this one). Foreground-forcing and resizing are
    deliberately not the same wait: forcing focus is only meaningful right
    when the window appears, while a resize is still worth applying late
    even if the user's already looking at the window by then."""
    try:
        import win32con
        import win32gui
    except ImportError:
        return

    target_name = os.path.basename(browser_exe).lower()
    hwnd = _find_new_window(before_hwnds, target_name)
    if hwnd is None:
        return

    _force_foreground(hwnd)

    geometry = _compute_reader_window_geometry(issue_id)
    if geometry and win32gui.IsWindow(hwnd):
        try:
            width, height, x, y = geometry
            win32gui.SetWindowPos(hwnd, 0, x, y, width, height, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
        except Exception:
            pass


def open_app_window(url, issue_id=None):
    """Opens `url` in a chromeless app-mode window rather than a browser tab.
    `issue_id`, if given (the reader launch path only), triggers a
    background pass that forces the window to the foreground and sizes it
    to that issue's page-1 dimensions — see _activate_and_resize_new_window."""
    exe = _find_app_browser_exe()

    # Windows denies SetForegroundWindow to a process that isn't itself
    # foreground and hasn't just received user input. The reader launch
    # path arrives via a background HTTP request to the control server
    # (triggered by a fetch() from whichever browser tab currently has
    # focus — the library), not direct user input to this tray process, so
    # without this the new window opens behind whatever's already focused.
    # Lifting the restriction for any process covers it regardless of
    # whether --app= spawns a fresh browser process or gets forwarded to an
    # already-running instance via IPC (the usual case once the browser's
    # already open, where the Popen'd PID isn't the one that ends up owning
    # the window anyway). Kept as a first line of defense even though
    # _activate_and_resize_new_window's AttachThreadInput-based force is the
    # one that's actually reliable — see its docstring.
    try:
        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    except Exception:
        pass

    if exe:
        before_hwnds = _snapshot_top_level_hwnds(os.path.basename(exe).lower()) if issue_id else None
        args = [exe, f"--app={url}"]
        try:
            subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            if issue_id:
                threading.Thread(
                    target=_activate_and_resize_new_window,
                    args=(before_hwnds, exe, issue_id),
                    daemon=True,
                ).start()
            return
        except OSError as e:
            log(f"App-mode launch failed ({e}), falling back to webbrowser.open().")
    webbrowser.open(url)

# digib00age brand mark (frontend/images/favicon.png) — reused here as the
# tray icon's base glyph. Square with a transparent background, unlike
# icon-oo.png/logo1.png (166x100 horizontal logotype), which don't fit a
# square tray icon. As of the 2026-07-28 rebrand close-out (DECISIONS.md)
# the tray app's process/menu name also reads "digib00age" — this comment
# previously carved out an exception (SPEC.md Section 1's 2026-07-07 scope
# note) keeping the name as "ComicVault" while only the glyph changed; that
# exception is superseded now that the rebrand covers all three surfaces.
FAVICON_PATH = os.path.join(PROJECT_ROOT, "frontend", "images", "favicon.png")
_base_icon_cache = None


def _frozen_server_executable_path():
    """Path to the sibling frozen server binary, for the packaged-installer
    build only (see DECISIONS.md "Windows MSI installer"). sys.executable
    is this tray binary itself once frozen, not a Python interpreter, so it
    can't run "start_server.py" as a script argument like the dev path
    does — the frozen server ships as its own separate exe alongside it."""
    exe_dir = os.path.dirname(sys.executable)
    exe_name = "digib00age-server.exe" if sys.platform == "win32" else "digib00age-server"
    return os.path.join(exe_dir, exe_name)


def start_reader():
    global reader_process
    log("Starting reader server subprocess...")
    # When this app runs under pythonw (no console), sys.stdout/stderr are None
    # in a child that inherits the same console-less state, which crashes any
    # print() call in start_server.py. Redirect to a file so the child always
    # has real stream objects.
    reader_log = open(READER_LOG_PATH, "a", encoding="utf-8")
    if getattr(sys, "frozen", False):
        command = [_frozen_server_executable_path()]
        cwd = os.path.dirname(sys.executable)
    else:
        command = [sys.executable, "start_server.py"]
        cwd = REPO_ROOT
    reader_process = subprocess.Popen(
        command,
        cwd=cwd,
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


class _ReaderControlHandler(BaseHTTPRequestHandler):
    """Handles GET /open-reader?id=<issue_id> from the web UI (frontend/js/
    app.js) — the only route this control server serves. Fire-and-forget:
    the caller uses fetch(..., {mode: 'no-cors'}) and doesn't read the body,
    it just needs to know whether the request reached a live listener at
    all (network reachability is the actual signal, not the response)."""

    def log_message(self, format, *args):
        pass  # BaseHTTPRequestHandler logs every request to stderr by default; skip it

    def do_GET(self):
        parsed = urlparse(self.path)
        issue_id = parse_qs(parsed.query).get("id", [None])[0]
        if parsed.path == "/open-reader" and issue_id and issue_id.isdigit():
            open_app_window(f"http://localhost:{READER_PORT}/reader/{issue_id}", issue_id=issue_id)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()


def start_control_server():
    try:
        server = HTTPServer(("127.0.0.1", TRAY_CONTROL_PORT), _ReaderControlHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        log(f"Reader-launch control server listening on 127.0.0.1:{TRAY_CONTROL_PORT}.")
    except OSError as e:
        # Non-fatal — app.js falls back to a plain window.open() popup (has
        # an address bar, but still usable) if this port can't be reached.
        log(f"Could not start reader-launch control server: {e}")


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


def _autostart_entry_path():
    """The OS-appropriate autostart entry path: the Windows Startup-folder
    shortcut, or the Linux ~/.config/autostart/ .desktop file."""
    return STARTUP_SHORTCUT_PATH if IS_WINDOWS else AUTOSTART_DESKTOP_PATH


def is_autostart_enabled(item=None):
    return os.path.exists(_autostart_entry_path())


def _autostart_target_path():
    """Shortcut target for the Windows Startup entry: the frozen tray exe
    itself for the packaged-installer build, start.bat for the normal
    dev/unfrozen path (see DECISIONS.md "Windows MSI installer") — there's
    no start.bat in a frozen install, so the shortcut has to point straight
    at the exe."""
    return sys.executable if getattr(sys, "frozen", False) else START_BAT_PATH


def _autostart_desktop_entry_contents():
    """.desktop file content for the Linux ~/.config/autostart entry (the
    freedesktop.org Desktop Entry spec), mirroring _autostart_target_path()'s
    frozen-vs-dev distinction: the frozen server binary's sibling frozen tray
    exe when packaged (see DECISIONS.md "Linux .deb release"), or `python3
    tray_app.py` for the normal dev/unfrozen path."""
    if getattr(sys, "frozen", False):
        exec_line = sys.executable
    else:
        script_path = os.path.join(PROJECT_ROOT, "tray", "tray_app.py")
        exec_line = f'{sys.executable} "{script_path}"'
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=digib00age\n"
        f"Exec={exec_line}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def _migrate_legacy_startup_shortcut():
    """One-time cleanup: removes the pre-rebrand ComicVault.lnk Startup entry
    if present, so it can't fire alongside a freshly created digib00age.lnk
    and double-launch the tray app. Safe no-op if it was never created or
    was already removed. Windows-only — no Linux install has ever had a
    pre-rebrand entry to migrate."""
    if not IS_WINDOWS:
        return
    if os.path.exists(LEGACY_STARTUP_SHORTCUT_PATH):
        try:
            os.remove(LEGACY_STARTUP_SHORTCUT_PATH)
            log("Removed legacy ComicVault.lnk Startup shortcut (superseded by digib00age.lnk).")
        except OSError as e:
            log(f"Failed to remove legacy autostart shortcut: {e}")


def _check_autostart_shortcut():
    """Logs a warning if the autostart entry exists but its target looks
    stale — e.g. after the install/repo folder moves (this happened on
    Windows 2026-08-04 when a shortcut created under the old
    private-dev-repo\\ layout kept pointing at a path that no longer
    existed, so autostart silently did nothing at login). Doesn't
    auto-repair: toggling "Start digib00age at login" off/on in the tray
    menu recreates it correctly in one click."""
    entry_path = _autostart_entry_path()
    if not os.path.exists(entry_path):
        return
    if IS_WINDOWS:
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            target = shell.CreateShortCut(entry_path).TargetPath
            expected = _autostart_target_path()
            if target != expected or not os.path.exists(target):
                log(
                    f"WARNING: autostart shortcut looks stale (points at {target!r}, "
                    f"expected {expected!r}, target exists: {os.path.exists(target)}). "
                    "Toggle 'Start digib00age at login' off then on in the tray menu to fix."
                )
        except Exception as e:
            log(f"Could not verify autostart shortcut: {e}")
    else:
        try:
            with open(entry_path, "r", encoding="utf-8") as f:
                contents = f.read()
            if contents != _autostart_desktop_entry_contents():
                log(
                    "WARNING: autostart .desktop entry looks stale (doesn't match "
                    "the current launch path). Toggle 'Start digib00age at login' "
                    "off then on in the tray menu to fix."
                )
        except OSError as e:
            log(f"Could not verify autostart .desktop entry: {e}")


def toggle_autostart(icon=None, item=None):
    """Creates or removes the OS-appropriate autostart entry (Windows
    Startup shortcut / Linux .desktop file). The entry's own existence is
    the source of truth for the menu checkbox — no config.json flag to keep
    in sync."""
    entry_path = _autostart_entry_path()
    if os.path.exists(entry_path):
        try:
            os.remove(entry_path)
            log("Autostart disabled (entry removed).")
        except OSError as e:
            log(f"Failed to remove autostart entry: {e}")
        return

    if IS_WINDOWS:
        try:
            import win32com.client  # imported lazily: a missing pywin32 shouldn't crash tray startup
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(entry_path)
            shortcut.TargetPath = _autostart_target_path()
            shortcut.WorkingDirectory = REPO_ROOT
            shortcut.WindowStyle = 7  # minimized
            shortcut.save()
            log("Autostart enabled (shortcut created).")
        except Exception as e:
            log(f"Failed to create autostart shortcut: {e}")
    else:
        try:
            os.makedirs(os.path.dirname(entry_path), exist_ok=True)
            with open(entry_path, "w", encoding="utf-8") as f:
                f.write(_autostart_desktop_entry_contents())
            os.chmod(entry_path, 0o755)
            log("Autostart enabled (.desktop entry created).")
        except OSError as e:
            log(f"Failed to create autostart .desktop entry: {e}")


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
    # "never call it at all." This is why "Start digib00age at login" below
    # can safely be a checkable item: its checkmark updates correctly on the
    # very next click with no extra code, since pystray already rebuilds the
    # menu after every click via the mechanism above.
    return pystray.Menu(
        pystray.MenuItem("digib00age", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Library", open_library),
        pystray.MenuItem("Admin", open_admin),
        pystray.MenuItem("Metadata Editor", open_editor),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start digib00age at login", toggle_autostart, checked=is_autostart_enabled),
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
    if IS_WINDOWS:
        _enable_dark_menu_support()

    log("=" * 40)
    log("digib00age tray app starting.")

    _migrate_legacy_startup_shortcut()
    _check_autostart_shortcut()

    start_reader()
    health_thread = threading.Thread(target=health_check_loop, daemon=True)
    health_thread.start()
    start_control_server()

    icon = pystray.Icon(
        "digib00age",
        make_icon_image("starting"),
        "digib00age",
        menu=build_menu(),
    )

    icon_thread = threading.Thread(target=update_icon_loop, args=(icon,), daemon=True)
    icon_thread.start()

    threading.Thread(target=wait_for_startup, daemon=True).start()

    icon.run()
    log("Tray icon stopped. Exiting.")


if __name__ == "__main__":
    main()
