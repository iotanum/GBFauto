#!/bin/bash

python3.11 -m venv ./venv
source venv/bin/activate
pip install --upgrade pip
pip install -r req --upgrade
playwright install
python -u launch.py
