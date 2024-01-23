@echo off

call py -m venv venv
call .\\venv\\Scripts\\activate.bat
call pip install --upgrade pip
call pip install -r requirements.txt --upgrade
call py main.py
pause