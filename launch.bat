@echo off

call python -m venv env
call .\env\bin\activate
call pip install --upgrade pip
call pip install -r requirements.txt
call python main.py