<#
.SYNOPSIS
    Scans a folder for directories containing multiple large files and generates a report.

.DESCRIPTION
    This script recursively scans a specified folder for subdirectories that contain 
    more than one file exceeding a defined minimum size (default 100 MB). It lists 
    those directories along with the count of large files and optionally saves a 
    report to a text file.

.PARAMETER folderPath
    The path to the root folder to scan for large files.

.PARAMETER minFileSize
    The minimum file size (in bytes) to consider a file "large". Default is 100 MB.

.PARAMETER reportPath
    Optional path for saving a report of directories with multiple large files.

.EXAMPLE
    .\FindLargeFileDirectories.ps1
    Scans "N:\Films" for directories with more than one file larger than 100 MB, 
    outputs the results, and saves a report to "N:\PotentialDuplicateMoviesReport.txt".

.NOTES
    - Useful for identifying directories that may contain duplicate or high-storage files.
    - Requires PowerShell.
#>

# Define the folder path to scan
$folderPath = "N:\Films"

# Minimum file size in bytes (100 MB)
$minFileSize = 100MB

# Initialize an array to store directories meeting the criteria
$matchingDirectories = @()

# Recursively scan the folder
Get-ChildItem -Path $folderPath -Recurse -Directory | ForEach-Object {
    $directory = $_.FullName
    # Get files in the directory larger than 100 MB
    $largeFiles = Get-ChildItem -Path $directory -File | Where-Object { $_.Length -gt $minFileSize }
    
    # Check if more than one file exceeds the size limit
    if ($largeFiles.Count -gt 1) {
        # Add the directory and file count to the results
        $matchingDirectories += @{
            Directory = $directory
            FileCount = $largeFiles.Count
        }
    }
}

# Display the results
if ($matchingDirectories.Count -gt 0) {
    Write-Output "Directories with more than one file larger than 100 MB:"
    $matchingDirectories | ForEach-Object {
        Write-Output "Directory: $($_.Directory), Files > 100MB: $($_.FileCount)"
    }
} else {
    Write-Output "No directories found with more than one file larger than 100 MB."
}

# Optional: Save the results to a file
$reportPath = "N:\PotentialDuplicateMoviesReport.txt"
$matchingDirectories | ForEach-Object {
    "Directory: $($_.Directory), Files > 100MB: $($_.FileCount)"
} | Set-Content -Path $reportPath

Write-Output "Report saved to $reportPath"