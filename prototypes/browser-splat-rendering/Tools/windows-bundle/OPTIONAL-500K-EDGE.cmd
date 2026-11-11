@echo off
rem VR-HE Toughbook browser test: optional 500,000-splat follow-up in Microsoft Edge, in a fresh
rem page. Run it only after RUN-EDGE.cmd has finished. See START-HERE.txt.
if not exist "%~dp0tools\launch.cmd" goto not_extracted
call "%~dp0tools\launch.cmd" run edge followup-500k
exit /b
:not_extracted
echo.
echo This file is still inside the ZIP. Close this window, right-click the ZIP file,
echo choose "Extract All...", then run this file from the extracted folder.
echo.
pause
exit /b 1
