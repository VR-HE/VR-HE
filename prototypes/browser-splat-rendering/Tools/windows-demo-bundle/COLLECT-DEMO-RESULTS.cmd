@echo off
rem VR-HE interactive browser demo: pack the results folder into one VRHE-demo-results-*.zip
rem file next to START-HERE-DEMO.txt, then show it in File Explorer. Browser profiles are not
rem included. See START-HERE-DEMO.txt.
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
