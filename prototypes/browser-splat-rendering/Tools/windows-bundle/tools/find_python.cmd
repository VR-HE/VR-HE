@echo off
rem VR-HE browser test: find Python 3.8 or newer without installing anything.
rem Sets VRHE_PY (the command that starts Python) and VRHE_PY_FROM (a description).
rem Order: an installed Python through the py launcher, then python or python3 on PATH, then
rem the portable Python in ..\runtime\python. Each candidate must start and import the modules
rem the test server needs. The Microsoft Store Python is skipped on purpose: it redirects
rem writes to the temporary folder, which the test must share with the browser.
rem The packager converts this file to CRLF line endings. Keep it ASCII only.
set "VRHE_PY="
set "VRHE_PY_FROM="
set "VRHE_PY_CHECK=import sys, ctypes, winreg, http.server, socketserver, zipfile, hashlib, json; sys.exit(0 if sys.version_info >= (3, 8) and 'WindowsApps' not in sys.executable else 1)"

py -3 -I -c "%VRHE_PY_CHECK%" >nul 2>&1
if errorlevel 1 goto try_python
set "VRHE_PY=py -3"
set "VRHE_PY_FROM=the Python installed on this computer, through the py launcher"
goto done

:try_python
python -I -c "%VRHE_PY_CHECK%" >nul 2>&1
if errorlevel 1 goto try_python3
set "VRHE_PY=python"
set "VRHE_PY_FROM=the Python installed on this computer"
goto done

:try_python3
python3 -I -c "%VRHE_PY_CHECK%" >nul 2>&1
if errorlevel 1 goto try_portable
set "VRHE_PY=python3"
set "VRHE_PY_FROM=the Python installed on this computer"
goto done

:try_portable
if not exist "%~dp0..\runtime\python\python.exe" goto done
"%~dp0..\runtime\python\python.exe" -I -c "%VRHE_PY_CHECK%" >nul 2>&1
if errorlevel 1 goto done
set VRHE_PY="%~dp0..\runtime\python\python.exe"
set "VRHE_PY_FROM=the portable Python included in this folder, runtime\python"

:done
set "VRHE_PY_CHECK="
exit /b 0
