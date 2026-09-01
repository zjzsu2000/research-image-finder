@echo off
setlocal
cd /d "%~dp0"

if exist "..\..\.spike-venv\Scripts\python.exe" (
  "..\..\.spike-venv\Scripts\python.exe" run_windows_gui.py
) else (
  py -3 run_windows_gui.py
)

if errorlevel 1 (
  echo.
  echo The prototype could not start. Confirm Python 3, Tkinter, NumPy, Pillow,
  echo and opencv-python-headless are installed, then share this window with the maintainer.
  pause
)
