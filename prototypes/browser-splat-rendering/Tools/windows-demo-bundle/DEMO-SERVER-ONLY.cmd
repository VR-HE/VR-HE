@echo off
rem VR-HE interactive browser demo (prototype): serve the demo at http://127.0.0.1:8791/ without
rem opening a browser, for the manual route in START-HERE-DEMO.txt. Ctrl+C stops it.
if not exist "%~dp0tools\launch.cmd" goto not_extracted
call "%~dp0tools\launch.cmd" serve
exit /b
:not_extracted
echo.
echo This file is still inside the ZIP. Close this window, right-click the ZIP file,
echo choose "Extract All...", then run this file from the extracted folder.
echo.
pause
exit /b 1
