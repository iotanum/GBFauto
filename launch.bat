@echo off

call py -m venv venv
call .\\venv\\Scripts\\activate.bat
call pip install --upgrade pip
call pip install -r req
call playwright install
call py launch.py
pause
