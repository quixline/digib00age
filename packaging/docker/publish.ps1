<#
.SYNOPSIS
    Build the digib00age Docker image and push it to the self-hosted registry on
    quixy, so other machines can install via setup.sh/setup.ps1 without git or a
    local build (see packaging/docker/README.txt).

.DESCRIPTION
    Run manually from the repo root on windy after testing locally - this is the
    only "release" step for Docker installs, there is no CI. Builds from the current
    working tree (same COPY pyproject.toml / COPY src/ context as docker-compose.yml's
    build:), tags it both with the version you pass and as :latest, and pushes both
    tags to digib00age.tech:5000.

    One-time prerequisite: Docker Desktop needs digib00age.tech:5000 (or quixy's LAN
    IP:5000) listed under "insecure-registries" in Settings > Docker Engine, since the
    registry is plain HTTP (LAN-only, no TLS) - e.g.:

        "insecure-registries": ["digib00age.tech:5000"]

    Docker Desktop needs a restart after that setting is added.

.PARAMETER Tag
    Version tag for this build, e.g. "v2.6.3-dev1". Required.

.EXAMPLE
    .\packaging\docker\publish.ps1 -Tag v2.6.3-dev1
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path "$PSScriptRoot\..\.."
$Registry = "digib00age.tech:5000/digib00age"

Write-Host "Building $Registry`:$Tag ..."
docker build -f "$PSScriptRoot\Dockerfile" -t "${Registry}:$Tag" -t "${Registry}:latest" $RepoRoot
if (-not $?) { throw "docker build failed" }

Write-Host "Pushing ${Registry}:$Tag ..."
docker push "${Registry}:$Tag"
if (-not $?) {
    throw "docker push failed - if this is 'server gave HTTP response to HTTPS client', " +
          "add digib00age.tech:5000 to Docker Desktop's insecure-registries (see script header) and restart Docker Desktop."
}

Write-Host "Pushing ${Registry}:latest ..."
docker push "${Registry}:latest"
if (-not $?) { throw "docker push (latest) failed" }

Write-Host "Done. ${Registry}:$Tag and :latest are live on quixy's registry."
