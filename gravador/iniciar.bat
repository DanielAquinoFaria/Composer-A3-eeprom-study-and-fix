@echo off
cd /d "%~dp0"
python -c "import tkinter, serial" >nul 2>&1
if errorlevel 1 (
  echo Instale Python 3.10 ou superior com Tcl/Tk e execute:
  echo python -m pip install -r requirements.txt
  pause
  exit /b 1
)
python desktop\app.py
if errorlevel 1 pause
