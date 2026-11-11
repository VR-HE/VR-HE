@echo off
rem VR-HE Toughbook browser test: pack the results folder into one VRHE-results-*.zip file
rem for the USB drive, then show it in File Explorer. See START-HERE.txt.
if not exist "%~dp0tools\launch.cmd" goto not_extracted
call "%~dp0tools\launch.cmd" collect
exit /b
:not_extracted
echo.
echo This file is still inside the ZIP. Close this window, right-click the ZIP file,
echo choose "Extract All...", then run this file from the extracted folder.
echo.
pause
exit /b 1
