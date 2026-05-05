#!/usr/bin/env bash
set -euo pipefail

python -m src.scripts.init_db
streamlit run src/ui/streamlit_app.py
