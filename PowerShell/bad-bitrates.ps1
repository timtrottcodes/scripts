<#
.SYNOPSIS
    Scans a directory of video files, identifies files with a high bitrate (MB per hour), 
    and copies them to a designated folder for further review.

.DESCRIPTION
    This script recursively scans a specified directory for video files (excluding MKV files), 
    calculates their size per hour of playback, and compares it to a user-defined threshold. 
    Files exceeding the threshold are copied to a target folder. A summary report is also 
    generated in CSV format.

.PARAMETER directory
    The path to the folder containing video files to scan.

.PARAMETER thresholdMBPerHour
    The bitrate threshold in MB per hour. Files above this value will be copied to the target folder.

.PARAMETER targetFolder
    The path to the folder where high-bitrate videos will be copied. The folder will be created if it does not exist.

.EXAMPLE
    .\HighBitrateVideos.ps1
    Scans "N:\Films" for high-bitrate videos, copies them to "C:\HighBitrateVideos", 
    and generates a CSV report.

.NOTES
    - Requires PowerShell and Windows COM Shell support.
    - Video duration is read via the Shell.Application COM object.
#>

# Set the directory to scan
$directory = "N:\Films"

# Set the threshold in MB per hour
$thresholdMBPerHour = 1400

# Set the target folder for copying large files
$targetFolder = "C:\HighBitrateVideos"

if (-not (Test-Path -Path $targetFolder)) {
    New-Item -Path $targetFolder -ItemType Directory | Out-Null
}

# Initialize the Shell COM object
$shell = New-Object -ComObject Shell.Application

# Function to get video duration in seconds
function Get-VideoDuration {
    param ($file)
    
    $folder = $shell.Namespace($file.DirectoryName)
    $item = $folder.ParseName($file.Name)
    
    # Video duration is usually at index 27
    $durationString = $folder.GetDetailsOf($item, 27)
    
    if ($durationString -match "(\d+):(\d+):(\d+)") {
        return [int]$matches[1] * 3600 + [int]$matches[2] * 60 + [int]$matches[3]
    } elseif ($durationString -match "(\d+):(\d+)") {
        return [int]$matches[1] * 60 + [int]$matches[2]
    } else {
        return $null
    }
}

# Scan for video files and check their encoding efficiency
$results = Get-ChildItem -Path $directory -Recurse -File | ForEach-Object {
    $file = $_
    
    # Exclude MKV files
    if ($file.Extension -ieq ".mkv") {
        return
    }

    $durationSec = Get-VideoDuration $file
    
    if ($durationSec -and $durationSec -gt 0) {
        $fileSizeMB = [math]::Round($file.Length / 1MB, 2)
        $durationHours = $durationSec / 3600
        $bitrateMBPerHour = [math]::Round($fileSizeMB / $durationHours, 2)
        
        if ($bitrateMBPerHour -gt $thresholdMBPerHour) {
            # Copy the file to the target folder
            $destinationPath = Join-Path -Path $targetFolder -ChildPath $file.Name
            Copy-Item -Path $file.FullName -Destination $destinationPath -Force

            [PSCustomObject]@{
                File = $file.FullName
                SizeMB = $fileSizeMB
                DurationHours = [math]::Round($durationHours, 2)
                BitrateMBPerHour = $bitrateMBPerHour
                CopiedTo = $destinationPath
            }
        }
    }
} 

# Output as a formatted table
$results | Format-Table -AutoSize

$logFile = "C:\HighBitrateVideos\VideoAnalysisReport.csv"
$results | Export-Csv -Path $logFile -NoTypeInformation
Write-Host "Report written to $logFile"
