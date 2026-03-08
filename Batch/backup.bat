rem xcopy "C:\Users\Tim Trott\AppData\Roaming\Adobe\Lightroom\Develop Presets\User Presets\*.*" "x:\windows\Lightroom\User Presets\" /V/C/E/H/R/K/D/Y/F/Z
rem xcopy "C:\Users\Tim Trott\AppData\Roaming\Adobe\Adobe Photoshop CS6\Presets\*.*" "x:\windows\Photoshop\Presets\" /V/C/E/H/R/K/D/Y/F/Z
rem xcopy "C:\Users\Tim Trott\Documents\Lightroom\*.*" "x:\windows\Lightroom\Catalog\" /V/C/E/H/R/K/D/Y/F/Z
rem xcopy "C:\Users\Tim Trott\Documents\Elder Scrolls Online\*.*" "x:\windows\Elder Scrolls Online\" /V/C/E/H/R/K/D/Y/F/Z
xcopy "C:\Users\Tim Trott\Documents\EVE\*.*" "x:\windows\EVE\User Documents\" /V/C/E/H/R/K/D/Y/F/Z
xcopy "C:\Users\Tim Trott\AppData\Local\CCP\EVE*.*" "x:\windows\EVE\AppData_Local\" /V/C/E/H/R/K/D/Y/F/Z
rem xcopy "C:\Users\Tim Trott\VirtualBox VMs\*.*" "x:\windows\VirtualBox VMs\" /V/C/E/H/R/K/D/Y/F/Z

"%ProgramFiles%\WinRAR\rar.exe" a -agYYYY-MM-DD -cfg- -ep1 -inul -m5 -r -y "x:\windows\Thunderbird\Thunderbird_Backup_.rar" "C:\Users\Tim Trott\AppData\Roaming\Thunderbird"

pause