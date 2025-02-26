#!/bin/bash

python3.13 -m venv ./venv
source venv/bin/activate
pip install --upgrade pip
pip install -r req --upgrade
PYTHON_JIT=1 python -u launch.py
