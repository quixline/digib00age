<#
.SYNOPSIS
    digib00age - one-line install (Windows, Docker Desktop already installed). No
    git, no source checkout, no build - pulls a pre-built image from the self-hosted
    registry on quixy and starts it.

.DESCRIPTION
    curl -fsSL http://digib00age.tech/setup.ps1 -o setup.ps1 ; Get-Content setup.ps1 ; .\setup.ps1

    (Fetch and read it before running it, same as any curl-piped installer.)

    See packaging/docker/README.txt for the full walkthrough, including the
    windy-only build/publish path this pulls from (publish.ps1).

.PARAMETER InstallDir
    Where to create config/ and data/ and drop docker-compose.yml. Defaults to
    .\digib00age in the current directory.
#>
param(
    [string]$InstallDir = ".\digib00age"
)

$ErrorActionPreference = "Stop"

$RegistryHost = "digib00age.tech:5000"
$InstallSite = "http://digib00age.tech"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "docker not found on PATH - install Docker Desktop first, then re-run this script."
    exit 1
}
docker compose version | Out-Null
if (-not $?) {
    Write-Error "docker compose (v2 plugin) not found - update Docker Desktop, then re-run this script."
    exit 1
}

# Reminder, not an automated check: Docker Desktop's daemon config + restart isn't
# reliably scriptable, so this is printed unconditionally rather than trying (and
# risking a false negative) to detect trust state first.
Write-Host ""
Write-Host "Note: Docker Desktop must trust $RegistryHost as an insecure (plain-HTTP) registry."
Write-Host "If the pull below fails with something like 'server gave HTTP response to HTTPS client':"
Write-Host "  1. Open Docker Desktop > Settings > Docker Engine"
Write-Host "  2. Add to the JSON: `"insecure-registries`": [`"$RegistryHost`"]"
Write-Host "  3. Apply & Restart Docker Desktop, then re-run this script."
Write-Host ""

Write-Host "Setting up $InstallDir ..."
New-Item -ItemType Directory -Force -Path "$InstallDir\config" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
Invoke-WebRequest -Uri "$InstallSite/docker-compose.yml" -OutFile "$InstallDir\docker-compose.yml"

Push-Location $InstallDir
try {
    Write-Host "Pulling image ..."
    docker compose pull
    if (-not $?) { throw "docker compose pull failed" }

    Write-Host "Starting digib00age ..."
    docker compose up -d
    if (-not $?) { throw "docker compose up failed" }
}
finally {
    Pop-Location
}

$hostIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } | Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "digib00age is starting - open http://$hostIp`:9800 once the container is up (docker compose logs -f to watch)."
