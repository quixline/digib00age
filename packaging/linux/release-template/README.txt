digib00age - Linux install
===========================

Run install.sh from inside this folder:

    ./install.sh

It checks for the system packages digib00age needs to install itself
(Linux distros vary too much for this to be fully automatic) and tells you
exactly what to install if anything's missing - then creates a private venv,
installs digib00age into it (this compiles a few small C extensions against
your own system's Python - takes under a minute), asks where to put it, and
sets up a menu launcher (Applications menu, or launch
<install dir>/venv/bin/digib00age-tray directly).

Prerequisites (checked automatically, fail-fast, before anything else runs):

    sudo apt install python3 python3-venv build-essential python3-dev git \
        python3-gi gir1.2-gtk-3.0 libayatana-appindicator3-1 \
        gir1.2-ayatanaappindicator3-0.1 python3-icu

digib00age itself is bundled in the sdist alongside this script - no
internet access is needed to fetch it. Its dependencies (fastapi, pillow,
etc.) are not bundled and are downloaded from PyPI during `pip install`, so
an internet connection is needed the first time you install.

To uninstall later, run the uninstall.sh script install.sh creates inside
your chosen install directory. Your library data
(~/.local/share/digib00age, ~/.config/digib00age) is left untouched.
