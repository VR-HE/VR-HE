@echo off
rem VR-HE interactive browser demo: shared part of the launchers in the main folder.
rem Usage: launch.cmd run ^<browser^>   or   launch.cmd serve   or   launch.cmd collect
rem Finds Python 3 (tools\find_python.cmd), then runs tools\demo_server.py with this folder as
rem the demo bundle. The server binds 127.0.0.1 port 8791 only, never uses port 9002, needs no
rem administrator rights, changes no settings and never stops a browser.
rem Paths are always quoted and never expanded inside parenthesized blocks, so folder names
rem with spaces, parentheses or ampersands work. The packager converts this file to CRLF.
setlocal
for %%I in ("%~dp0..") do set "VRHE_ROOT=%%~fI"
set "VRHE_EXIT=1"
if not exist "%VRHE_ROOT%\app\index.html" goto incomplete
if not exist "%VRHE_ROOT%\tools\demo_server.py" goto incomplete
if not exist "%VRHE_ROOT%\tools\browser_test_harness.py" goto incomplete
if not exist "%VRHE_ROOT%\bundle.json" goto incomplete
cd /d "%VRHE_ROOT%"
call "%~dp0find_python.cmd"
if not defined VRHE_PY goto no_python
echo Using %VRHE_PY_FROM%.
if /i "%~1"=="run" goto run
if /i "%~1"=="serve" goto serve
if /i "%~1"=="collect" goto collect
echo Unknown launcher command: %1
goto finish

:run
title VR-HE interactive demo - %2
%VRHE_PY% -I "%VRHE_ROOT%\tools\demo_server.py" run --bundle "%VRHE_ROOT%" --browser %2
set "VRHE_EXIT=%errorlevel%"
goto finish

:serve
title VR-HE interactive demo - server only
%VRHE_PY% -I "%VRHE_ROOT%\tools\demo_server.py" serve --bundle "%VRHE_ROOT%"
set "VRHE_EXIT=%errorlevel%"
goto finish

:collect
title VR-HE interactive demo - collect results
%VRHE_PY% -I "%VRHE_ROOT%\tools\demo_server.py" collect --bundle "%VRHE_ROOT%"
set "VRHE_EXIT=%errorlevel%"
goto finish

:incomplete
echo.
echo Some demo files are missing from this folder.
echo Delete this folder, right-click the ZIP file, choose "Extract All..." and run the
echo launcher from the newly extracted folder.
goto finish

:no_python
echo.
echo Python 3 could not be started on this computer, so the demo cannot run.
echo   - No installed Python 3.8 or newer was found, and
if exist "%VRHE_ROOT%\runtime\python\python.exe" goto portable_blocked
echo   - the portable Python is missing from the runtime folder. Extract the ZIP again.
goto finish

:portable_blocked
echo   - the portable Python in the runtime folder did not start. Windows or security
echo     settings may block programs started from this folder.
echo Do not change security settings to get around this. Note this message and report it.
goto finish

:finish
echo.
echo Press any key to close this window.
pause >nul
endlocal & exit /b %VRHE_EXIT%
