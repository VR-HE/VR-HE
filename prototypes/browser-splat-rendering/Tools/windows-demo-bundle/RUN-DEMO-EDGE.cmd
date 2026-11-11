@echo off
rem VR-HE interactive browser demo (prototype): open the demo in Microsoft Edge. See START-HERE-DEMO.txt.
rem Uses a separate demo profile kept in %LOCALAPPDATA%\VRHE-Interactive-Demo so that saved
rem demo records are still there next time. Your own Microsoft Edge windows and profile are not touched.
if not exist "%~dp0tools\launch.cmd" goto not_extracted
call "%~dp0tools\launch.cmd" run edge
exit /b
:not_extracted
echo.
echo This file is still inside the ZIP. Close this window, right-click the ZIP file,
echo choose "Extract All...", then run this file from the extracted folder.
echo.
pause
exit /b 1
