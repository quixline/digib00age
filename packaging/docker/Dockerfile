# digib00age - Docker image (server + web frontend only; see
# packaging/docker/README.txt for scope). Multi-stage: builder installs the
# app into a venv, runtime stage copies just that venv across so the final
# image doesn't carry build tools/headers.
#
# Build from the repo root (needs pyproject.toml + src/ in the build
# context):
#   docker build -f packaging/docker/Dockerfile -t digib00age .
# or via packaging/docker/docker-compose.yml (build: context set to repo root).
#
# Base is Ubuntu, not a pyenv-built python:*-slim image, deliberately: the
# system's apt-installed python3-icu package (comictagger's PyICU dependency
# - no portable prebuilt PyPI wheel, see preflight-runtime.sh's comment on
# the Linux sdist install path) is compiled against Ubuntu's own packaged
# Python build and must match it ABI-wise. A --system-site-packages venv
# lets pip see that apt-installed python3-icu as already satisfying
# comictagger's requirement instead of trying (and failing without
# libicu-dev/pkg-config) to build pyicu from source.
#
# No GTK/AppIndicator apt packages here on purpose, unlike the Linux desktop
# install (README.md's python3-gi/gir1.2-appindicator list): this image's
# entrypoint is digib00age-server (backend.cli:main), which never imports
# the tray package, so pystray is never actually loaded at runtime. pystray's
# own "appindicator" extra is a pip no-op anyway (pystray does not declare
# it - pip installs plain pystray and warns, confirmed empirically building
# the Linux sdist release), so pip install . doesn't need those system
# packages either. If a future change makes the server import tray code
# unconditionally, this assumption needs revisiting.

FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-dev \
        python3-icu \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml ./
COPY src/ ./src/

# --system-site-packages so apt's python3-icu (above) is visible to pip's
# dependency resolver - see file header. --upgrade pip first: Ubuntu 24.04's
# system pip is old enough to mishandle some of this project's dependency
# markers.
RUN python3 -m venv --system-site-packages /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install .

FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-icu \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# XDG paths - config.py's _USE_XDG_PATHS mechanism resolves config/DB/
# thumbnails under these automatically for a genuine pip-installed
# distribution (see the Docker scoping plan; no code change needed here).
# Bind-mount these to real host directories via docker-compose.yml.
ENV XDG_CONFIG_HOME=/config
ENV XDG_DATA_HOME=/data
RUN mkdir -p /config /data

# Tells config.py this is a Docker container (not a bare-metal pip install,
# which is otherwise indistinguishable — both are _IS_PIP_INSTALLED) so it can
# pre-seed library_root as /library on first boot. See config.py's _IS_DOCKER.
ENV DIGIB00AGE_DOCKER=1

# Runs as root, deliberately - matches this project's other install paths
# (the Windows MSI and Linux .deb/sdist both run as the installing user
# directly, no privilege separation). A non-root user here just breaks on
# first run instead: Docker auto-creates an absent bind-mount host
# directory as root:root, so a container-side app user can't write into
# ./config or ./data unless the host path is pre-chowned by hand first -
# not worth the friction for a single-user self-hosted tool.
EXPOSE 9800

ENTRYPOINT ["digib00age-server"]
