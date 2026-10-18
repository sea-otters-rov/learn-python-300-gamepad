#Requires -Version 5.1
<#
.SYNOPSIS
    Copy the whole board\ folder onto the attached XIAO RP2350.

.DESCRIPTION
    board\ is an exact image of the board's root. This copies everything that
    changed; -Clean also DELETES anything on the board that is not in board\.
    (A single saved file goes through tools\sync.py instead, which is faster.)

    Only a board whose boot_out.txt says "Board ID:seeeduino_xiao_rp2350" is
    touched. A MatrixPortal from Parts 1-2 plugged in at the same time is left
    alone -- with -Clean, anything else would wipe its lessons.

.EXAMPLE
    & .\tools\sync.ps1

.EXAMPLE
    & .\tools\sync.ps1 -Clean
    Use on a fresh board, or one with files from somewhere else, to make it
    match board\ exactly.
#>
[CmdletBinding()]
param([switch]$Clean)

$ErrorActionPreference = 'Stop'
$src = (Resolve-Path (Join-Path $PSScriptRoot '..\board')).Path.TrimEnd('\')
$Supported = @('seeeduino_xiao_rp2350')  # keep in step with tools\find_board.py

function Get-BoardId {
    # The "Board ID:" line from boot_out.txt, which CircuitPython writes itself.
    # Empty for anything that is not a CircuitPython board.
    param([string]$Root)
    $f = Join-Path $Root 'boot_out.txt'
    if (-not (Test-Path $f)) { return '' }
    $text = Get-Content $f -Raw
    if ($text -notlike 'Adafruit CircuitPython*') { return '' }
    if ($text -match '(?m)^Board ID:(\S+)') { return $Matches[1] }
    return ''
}

function Repair-Bom {
    # CircuitPython cannot parse a UTF-8 BOM, and robocopy copies verbatim, so
    # fix it in the source. See tools\sync.py.
    param([string[]]$Paths)
    foreach ($p in $Paths) {
        $b = [System.IO.File]::ReadAllBytes($p)
        if ($b.Length -lt 3 -or $b[0] -ne 0xEF -or $b[1] -ne 0xBB -or $b[2] -ne 0xBF) { continue }
        $rest = New-Object byte[] ($b.Length - 3)
        [Array]::Copy($b, 3, $rest, 0, $rest.Length)
        [System.IO.File]::WriteAllBytes($p, $rest)
        Write-Host "[sync] stripped a UTF-8 BOM from $(Split-Path $p -Leaf)" -ForegroundColor Yellow
    }
}

# [System.IO.DriveInfo] is a direct Win32 call (~40 ms). Get-Volume goes through
# WMI and takes seconds.
$targets = @()
foreach ($d in [System.IO.DriveInfo]::GetDrives()) {
    if (-not $d.IsReady -or $d.DriveType -ne [System.IO.DriveType]::Removable) { continue }
    $id = Get-BoardId $d.RootDirectory.FullName
    if (-not $id) { continue }
    if ($Supported -contains $id) { $targets += $d }
    else { Write-Host "[sync] leaving alone: $($d.Name) ($id)" -ForegroundColor DarkGray }
}
if ($targets.Count -eq 0) {
    Write-Host "[sync] No XIAO RP2350 found." -ForegroundColor Yellow
    Write-Host "       Check the USB cable is a DATA cable, not charge-only." -ForegroundColor Yellow
    Write-Host "       If the board is in the bootloader, press reset once." -ForegroundColor Yellow
    exit 1
}

Repair-Bom -Paths (Get-ChildItem $src -Recurse -Filter *.py -File).FullName

foreach ($drive in $targets) {
    $dst = $drive.RootDirectory.FullName.TrimEnd('\')
    if ($Clean) {
        # /XD folders are invisible to robocopy, so /PURGE never removes them.
        Get-ChildItem -Path $dst -Directory -Recurse -Force -Filter '__pycache__' -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    # /FFT compares timestamps at FAT's 2-second granularity.
    # boot_out.txt is written by the board itself; never touch it.
    $rb = @(
        $src, $dst, '/E', '/FFT', '/R:2', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP',
        '/XD', '__pycache__', '.git', 'System Volume Information', '.Trashes', '.fseventsd',
        '/XF', 'boot_out.txt', '.metadata_never_index', '.Trash-1000'
    )
    if ($Clean) { $rb += '/PURGE' }
    & robocopy @rb | Out-Null
    if ($LASTEXITCODE -ge 8) {
        Write-Host "[sync] robocopy failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    $freeKB = [math]::Round((New-Object System.IO.DriveInfo $drive.Name).AvailableFreeSpace / 1KB)
    $verb = if ($Clean) { 'synced (clean)' } else { 'synced' }
    Write-Host "[sync] board\ $verb -> $dst  ($freeKB KB free)" -ForegroundColor Green
}

# robocopy's 1 and 2 mean "copied" and "extras found" -- both success. Do not
# leak them as this script's exit code.
exit 0
