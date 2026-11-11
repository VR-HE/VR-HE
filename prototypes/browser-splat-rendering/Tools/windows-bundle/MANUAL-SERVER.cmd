@echo off
rem VR-HE Toughbook browser test: manual fallback. Starts only the local test server
rem (127.0.0.1); you open the browser yourself. See "Manual fallback" in START-HERE.txt.
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
