<#
.SYNOPSIS
    digib00age - two-line install (Windows, Docker Desktop already installed). No
    git, no source checkout, no build - pulls the pre-built public image from
    GitHub Container Registry and starts it.

.DESCRIPTION
    From a normal (non-elevated) folder, in cmd.exe or PowerShell - both work:

        curl.exe -fsSL https://github.com/quixline/digib00age/releases/download/v1-beta/setup.ps1 -o setup.ps1
        powershell -ExecutionPolicy Bypass -File setup.ps1

    (Fetch and read it before running it, same as any curl-fetched installer -
    `type setup.ps1` in cmd.exe or `Get-Content setup.ps1` in PowerShell.)

    Two separate commands deliberately, not chained with `;` or `&&`: Windows
    PowerShell 5.1 doesn't support `&&`, and cmd.exe doesn't support `;`, so no
    single one-liner runs in both. `curl.exe` (not plain `curl`) avoids
    PowerShell's built-in `Invoke-WebRequest` alias, which doesn't understand
    `-fsSL`. `powershell -File` (not `.\setup.ps1`) works from cmd.exe too,
    where a .ps1 can't be run directly.

    See packaging/docker/README.txt for the full walkthrough, including the
    windy-only build/publish path this pulls from (publish.ps1). GHCR is real
    TLS - no insecure-registry trust step needed, unlike the old quixy-registry
    rehearsal this replaced.

.PARAMETER InstallDir
    Where to create config/ and data/ and drop docker-compose.yml. Defaults to
    .\digib00age in the current directory.
#>
param(
    [string]$InstallDir = ".\digib00age"
)

$ErrorActionPreference = "Stop"

$ReleaseTag = "v1-beta"
$ComposeUrl = "https://github.com/quixline/digib00age/releases/download/$ReleaseTag/docker-compose.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "docker not found on PATH - install Docker Desktop first, then re-run this script."
    exit 1
}
docker compose version | Out-Null
if (-not $?) {
    Write-Error "docker compose (v2 plugin) not found - update Docker Desktop, then re-run this script."
    exit 1
}

Write-Host "Setting up $InstallDir ..."
New-Item -ItemType Directory -Force -Path "$InstallDir\config" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
Invoke-WebRequest -Uri $ComposeUrl -OutFile "$InstallDir\docker-compose.yml"

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
