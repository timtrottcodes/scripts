# Source and destination
$Source      = "Y:\"
$Destination = "K:\megadrive"

# Create destination if it does not exist
if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

# Robocopy options:
# /MIR      - Mirror directory tree (copies new/changed files, deletes removed files)
# /Z        - Restartable mode (resumable if interrupted)
# /R:2      - Retry twice on failed copies
# /W:5      - Wait 5 seconds between retries
# /MT:1    - Multithreaded copy (adjust 8–32 depending on system/network)
# /COPY:DAT - Copy Data, Attributes, Timestamps (safe default)
# /DCOPY:T  - Preserve directory timestamps
# /FFT      - Tolerate timestamp differences on network shares
# /XA:SH    - Exclude system and hidden files
# /LOG+:    - Append to log file

$LogFile = "D:\robocopy.log"

robocopy `
    $Source `
    $Destination `
    /MIR `
    /Z `
    /R:0 `
    /W:0 `
    /MT:1 `
    /COPY:DAT `
    /DCOPY:T `
    /FFT `
    /XA:SH `
    /V

# Capture Robocopy exit code
$ExitCode = $LASTEXITCODE

# Robocopy exit codes below 8 are success conditions
if ($ExitCode -lt 8) {
    Write-Host "Backup completed successfully. Exit code: $ExitCode"
} else {
    Write-Warning "Backup completed with errors. Exit code: $ExitCode"
}
