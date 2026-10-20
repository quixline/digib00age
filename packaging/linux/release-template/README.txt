digib00age - Linux install
===========================

Set the file permissions and run install.sh from inside this folder:

	chmod +x install.sh && ./install.sh 

It checks for the system packages digib00age needs to install itself
(Linux distros vary too much for this to be fully automatic) and tells you
exactly what to install if anything's missing - then creates a private venv,
installs digib00age into it (this compiles a few small C extensions against
your own system's Python - takes under a minute), asks where to put it, and
sets up a menu launcher (Applications menu, or launch
<install dir>/venv/bin/digib00age-tray directly).

Prerequisites (checked automatically, fail-fast, before anything else runs):

    sudo apt install python3 python3-venv build-essential python3-dev \
        python3-gi gir1.2-gtk-3.0 libayatana-appindicator3-1 \
        gir1.2-ayatanaappindicator3-0.1 python3-icu

Run that apt command with sudo as shown - but run install.sh itself as
yourself, without sudo. It installs into your own home directory and sets
up your own Applications-menu entry; running it as root writes those into
root's profile instead, where your desktop session never sees them.

digib00age itself is bundled in the sdist alongside this script - no
internet access is needed to fetch it. Its dependencies (fastapi, pillow,
etc.) are not bundled and are downloaded from PyPI during `pip install`, so
an internet connection is needed the first time you install.

To uninstall later, run the uninstall.sh script install.sh creates inside
your chosen install directory. Your library data
(~/.local/share/digib00age, ~/.config/digib00age) is left untouched.

If you also install digib00age as a browser PWA (Admin page's "Install App"
button, or your browser's own install icon) and the taskbar/Alt-Tab icon
shows a generic browser icon instead of digib00age's own, your desktop's
icon cache probably just needs a refresh - GTK-based desktops (Cinnamon,
GNOME, COSMIC, etc.) don't always pick up a newly-installed app's icon
automatically. Run:

    gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

then log out and back in (or restart your desktop panel) and the real icon
should appear.
