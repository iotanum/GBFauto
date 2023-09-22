@echo off

call py -m venv venv
call .\\venv\\Scripts\\activate.bat
call pip install --upgrade pip
call pip install -r requirements.txt --upgrade
call pip install --force-reinstall -v "selenium==4.6.0"
call py main.py
pause