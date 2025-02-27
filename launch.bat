@echo off

call uv pip install -r pyproject.toml
call .\\venv\\Scripts\\activate.bat
call playwright install
call uv run launch.py
pause
