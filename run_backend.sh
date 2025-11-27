#!/bin/bash
# Run StudySync Backend

echo "Starting StudySync Backend..."
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
