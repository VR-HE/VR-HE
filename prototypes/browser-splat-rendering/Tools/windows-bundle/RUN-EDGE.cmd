@echo off
rem VR-HE Toughbook browser test: baseline test in Microsoft Edge. See START-HERE.txt.
rem Opens Edge with a fresh temporary profile; your own Edge windows and profile are not touched.
if not exist "%~dp0tools\launch.cmd" goto not_extracted
call "%~dp0tools\launch.cmd" run edge baseline
exit /b
:not_extracted
echo.
echo This file is still inside the ZIP. Close this window, right-click the ZIP file,
echo choose "Extract All...", then run this file from the extracted folder.
echo.
pause
exit /b 1
