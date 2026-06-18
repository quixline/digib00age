"""
ComicVault Tray App — launches the reader server and sits in the system tray.

Run from the project root:
    python tray\\tray_app.py        (console visible, for debugging)
    pythonw tray\\tray_app.py       (silent, for normal/startup use)

Tray icon (left or right click) shows a menu with:
    - Open Library
    - Admin
    - Metadata Editor   (opens the URL only — does not launch/manage that process)
    - Stop ComicVault

Reader status (starting/running/stopped) is shown via the tray icon's
coloured dot (yellow/green/red), not via the menu text — see build_menu()
for why the menu label is intentionally static.

A background thread checks the reader server every 30 seconds and restarts
it if the process has died.
"""

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

state_lock = threading.Lock()
reader_process = None
reader_status = "starting"  # "starting" | "running" | "stopped"
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
        if proc is None:
            continue
        if proc.poll() is not None:
            log(f"Reader process exited (code {proc.returncode}). Restarting.")
            with state_lock:
                reader_status = "starting"
            start_reader()
            wait_for_startup()
        else:
            with state_lock:
                reader_status = "running" if port_is_open(READER_PORT) else "stopped"


def make_icon_image(status):
    color_map = {
        "running": (66, 200, 110),
        "starting": (230, 180, 50),
        "stopped": (220, 70, 70),
    }
    dot_color = color_map.get(status, (150, 150, 150))

    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Simple book/comic glyph in the accent colour
    accent = (139, 110, 245)
    draw.rounded_rectangle([8, 6, 56, 58], radius=8, fill=accent)
    draw.rectangle([14, 14, 50, 18], fill=(255, 255, 255, 200))
    draw.rectangle([14, 24, 42, 28], fill=(255, 255, 255, 160))
    draw.rectangle([14, 34, 46, 38], fill=(255, 255, 255, 160))

    # Status dot, bottom-right
    draw.ellipse([40, 40, 60, 60], fill=dot_color, outline=(20, 20, 20, 255))

    return image


def open_library(icon=None, item=None):
    webbrowser.open(f"http://localhost:{READER_PORT}")


def open_admin(icon=None, item=None):
    webbrowser.open(f"http://localhost:{READER_PORT}/admin")


def open_editor(icon=None, item=None):
    # Editor is part of the same FastAPI app, no separate process/port
    # (EDITOR_SPEC.md Section 2) — was http://localhost:{EDITOR_PORT} (8001).
    webbrowser.open(f"http://localhost:{READER_PORT}/editor")


def stop_comicvault(icon, item=None):
    log("Stop requested from tray menu.")
    stop_event.set()
    with state_lock:
        proc = reader_process
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    icon.stop()


def build_menu():
    # Status is conveyed only via the tray icon's coloured dot (see
    # make_icon_image / update_icon_loop), not via a live-updating menu label.
    # pystray's Windows backend caches one native menu handle and only
    # rebuilds it when icon.update_menu() runs; calling that on a timer raced
    # with the user having the context menu open and corrupted the native
    # menu's command-ID -> callback mapping, so a click on "Admin" could
    # actually fire "Open Library"'s callback. Swapping icon.icon does not
    # touch the menu handle at all, so it carries no such risk. See SPEC.md
    # change log 2026-06-17 (Admin link opening Home).
    return pystray.Menu(
        pystray.MenuItem("ComicVault", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Library", open_library),
        pystray.MenuItem("Admin", open_admin),
        pystray.MenuItem("Metadata Editor", open_editor),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Stop ComicVault", stop_comicvault),
    )


def update_icon_loop(icon):
    last_status = None
    while not stop_event.wait(2):
        with state_lock:
            status = reader_status
        if status != last_status:
            icon.icon = make_icon_image(status)
            last_status = status


def main():
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
