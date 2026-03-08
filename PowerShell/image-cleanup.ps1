$Path = "C:\Users\ttrott\Downloads\"

function Show-Menu {
    param (
        [string]$Title = 'My Menu'
    )
    Clear-Host
    Write-Host "================ $Title ================"

    Write-Host ""
    Write-Host "1: Scan for images not in subfolders"
    Write-Host "2: Remove .jpg where RAW also exists in same folder"
    Write-Host "3: Remove duff files (.jbf, .db, ...)"
    Write-Host "4: Remove empty folders"
    Write-Host ""
    Write-Host "Q: Press 'Q' to quit."
}

function Clear-Raw {
    $remove = $false
    $parisFound = $false

    $logFile = "$PSScriptRoot\raw+jpeg.log"
    Remove-Item $logFile -ErrorAction SilentlyContinue

    $test = Read-Host "Remove JPEGs from RAW+JPEG pairs (y/n) [n]"
    if( $test.CompareTo("y") -eq 0 ) {
        $remove = $true
        echo "Will delete matches when found."
    }

    $dirs = gci $script:path -Directory -Recurse
    $dirs | foreach-object {
        $searchPath = $_.FullName
        $jobs = gci "$searchPath\*.*" -include *.raw,*.cr2,*.dng,*.nef | select -expand basename | sort -unique
        $jobs | foreach-object {
            if( ((Test-Path -path "$searchPath\$_.raw") -and (Test-Path -path "$searchPath\$_.jpg")) -or
                ((Test-Path -path "$searchPath\$_.cr2") -and (Test-Path -path "$searchPath\$_.jpg")) -or
                ((Test-Path -path "$searchPath\$_.nef") -and (Test-Path -path "$searchPath\$_.jpg" )) -or
                ((Test-Path -path "$searchPath\$_.dng") -and (Test-Path -path "$searchPath\$_.jpg" ))
            )
            {
                $pairsFound = $true;
                echo "Matches: $searchPath\$_.jpg" | Tee-Object $logFile -Append
                if( $remove ) {
                    echo "Removing: $searchPath\$_.jpg" | Tee-Object $logFile -Append
                    Remove-Item $searchPath\$_.jpg
                }
            }
        }
    }

    if( -not $pairsFound ) {
        echo "No RAW+JPEG pairs found."
    }
}

do
{
    Show-Menu
    $input = Read-Host "Please select a task by number Or Q to Quit"
    switch ($input)
    {
        '1' {
             $folders = Get-ChildItem -Recurse | ?{ $_.PSIsContainer }
             $folders | ForEach-Object {
                 $hasfolders = (Get-ChildItem -Path "$($_.FullName)" | ?{ $_.PSIsContainer } | Measure-Object).Count
                 $hasfiles = (Get-ChildItem -Path "$($_.FullName)" | ?{ !$_.PSIsContainer } | Measure-Object).Count

                 If (($hasfolders -gt 0) -And ($hasfiles -gt 0)) {
                    Write-Host "$($_.FullName)"
                 }
             }
        }
        '2' {
            cls
            Clear-Raw
        }
        '3' {
            cls
            Get-ChildItem -Path $Path -Include Thumbs.db -Recurse -Force | Remove-Item -Force
            Get-ChildItem -Path $Path -Include pspbrowse.jbf -Recurse -Force | Remove-Item -Force
            Get-ChildItem -Path $Path -Include desktop.ini -Recurse -Force | Remove-Item -Force
        }
        '4' {
            $dirs = gci $Path -directory -recurse | Where { (gci $_.fullName).count -eq 0 } | select -expandproperty FullName
            $dirs | Foreach-Object { Remove-Item $_ }
        }
        'q' {
            return
        }
    }
    pause
}
until ($input -eq 'q')