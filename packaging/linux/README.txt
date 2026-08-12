digib00age - Linux packaging
=============================

This folder has two different audiences.

For Tez: building a release (needs the full repo + a build toolchain)
-----------------------------------------------------------------------
Run make_release.sh. It freezes both binaries from source and produces
dev/distros/digib00age-linux-install.zip - a small, self-contained folder
end users can download, unzip, and run, with no repo and no build toolchain
of their own. Prerequisites (checked automatically, fail-fast, before
anything else runs - see preflight-build.sh):

    sudo apt install python3 python3-venv python3-gi gir1.2-gtk-3.0 \
        libayatana-appindicator3-1

Why these matter at build time:
- python3 / python3-venv: the build venv used to freeze the app with
  PyInstaller.
- python3-gi (PyGObject) is required at FREEZE time. PyInstaller's static
  analysis needs to actually import `gi` to bundle pystray's AppIndicator
  backend. If it's missing, the freeze doesn't error - it silently produces
  a tray with no working menu (a real bug this project hit once, BUG-040).
- gir1.2-gtk-3.0 / libayatana-appindicator3-1: also needed at build time -
  freeze.sh's PyInstaller hook actually imports pystray during analysis to
  pick the right backend, which needs these importable.

install.sh (this folder, not the release zip) is also available as a
dev-machine convenience - builds and installs directly from a full checkout
without producing a zip. build.sh (produces a .deb) is a third,
secondary/reference path - see DECISIONS.md "Installer: user-selectable
install directory".

Headless / SSH builds: set DISPLAY before running any of the above (e.g.
`export DISPLAY=:0`) - freeze.sh's PyInstaller hook needs a live X DISPLAY
for pystray's backend probe to resolve correctly.

For end users: installing digib00age (needs nothing but the release zip)
-----------------------------------------------------------------------
Download digib00age-linux-install.zip, unzip it, and run the install.sh
inside it (release-template/install.sh, before zipping). That installer is
entirely separate from this folder's - no repo, no Python, no build
toolchain. It only checks for the three runtime GTK/tray libraries
(python3-gi, gir1.2-gtk-3.0, libayatana-appindicator3-1) and tells you
what to install if anything's missing.
