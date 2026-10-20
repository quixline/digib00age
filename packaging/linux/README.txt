digib00age - Linux packaging
=============================

This folder has two different audiences.

For Tez: building a release (needs the full repo, not a build toolchain)
-----------------------------------------------------------------------
Run make_release.sh. It builds a pip sdist from src/ (source only, no
compiled binaries - see DECISIONS.md "Linux packaging: PyInstaller -> sdist"
for why: a frozen binary is tied to the build machine's exact Python ABI and
breaks on any target with a different Python version) and produces
dev/distros/digib00age-linux-install.zip - a small, self-contained folder
end users can download, unzip, and run, with no repo of their own.
Prerequisite on the build machine itself:

    pip install build

install.sh (this folder, not the release zip) is also available as a
dev-machine convenience - builds the sdist and installs it directly, without
producing a zip.

For end users: installing digib00age (needs nothing but the release zip)
-----------------------------------------------------------------------
Download digib00age-linux-install.zip, unzip it, and run the install.sh
inside it (release-template/install.sh, before zipping). It creates a
private venv and `pip install`s digib00age into it - this compiles a
handful of small C extensions against the end user's own Python (the whole
point of the sdist approach: no build-machine/Python-version mismatch is
possible, since compilation happens locally). Checked automatically,
fail-fast, before anything else runs (see release-template/preflight-runtime.sh):

    sudo apt install python3 python3-venv build-essential python3-dev git \
        python3-gi gir1.2-gtk-3.0 libayatana-appindicator3-1 \
        gir1.2-ayatanaappindicator3-0.1 python3-icu

Note: packaging/linux/build.sh (the .deb path) and packaging/linux/debian/
are stale as of this pivot - they depended on the now-deleted
preflight-build.sh/freeze.sh (PyInstaller) scripts and were already broken
by the same Python-ABI issue driving this whole change. Left as-is, not
maintained; out of scope for now.
