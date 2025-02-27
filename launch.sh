#!/bin/bash

uv pip install -r pyproject.toml
source .venv/bin/activate
playwright install
uv run launch.py
