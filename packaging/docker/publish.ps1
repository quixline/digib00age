<#
.SYNOPSIS
    Build the digib00age Docker image and push it to GitHub Container Registry
    (GHCR), so other machines can install via setup.sh/setup.ps1 or a plain
    `docker pull` with no git or local build (see packaging/docker/README.txt).

.DESCRIPTION
    Run manually from the repo root on windy after testing locally - this is the
    only "release" step for Docker installs, there is no CI. Builds from the current
    working tree (same COPY pyproject.toml / COPY src/ context as docker-compose.yml's
    build:), tags it both with the version you pass and as :latest, and pushes both
    tags to ghcr.io/quixline/digib00age.

    One-time prerequisite: `docker login ghcr.io` with a GitHub Personal Access
    Token that has `write:packages` scope. GHCR is real TLS, so no
    insecure-registries setting is needed (unlike the old quixy-registry path).

.PARAMETER Tag
    Version tag for this build, e.g. "v1-beta". Required.

.EXAMPLE
    .\packaging\docker\publish.ps1 -Tag v1-beta
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path "$PSScriptRoot\..\.."
$Registry = "ghcr.io/quixline/digib00age"

Write-Host "Building $Registry`:$Tag ..."
docker build -f "$PSScriptRoot\Dockerfile" -t "${Registry}:$Tag" -t "${Registry}:latest" $RepoRoot
if (-not $?) { throw "docker build failed" }

Write-Host "Pushing ${Registry}:$Tag ..."
docker push "${Registry}:$Tag"
if (-not $?) {
    throw "docker push failed - if this is an auth error, run 'docker login ghcr.io' " +
          "with a PAT that has write:packages scope first."
}

Write-Host "Pushing ${Registry}:latest ..."
docker push "${Registry}:latest"
if (-not $?) { throw "docker push (latest) failed" }

Write-Host "Done. ${Registry}:$Tag and :latest are live on GHCR."
Write-Host "Remember: the GHCR package visibility must be set to Public (once) for anonymous pulls to work - Package settings on GitHub, Danger Zone."
