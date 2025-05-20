#!/bin/bash

# Kill any running uvicorn processes
pkill -f 'uvicorn main:app'

# Set API keys
export MISTRAL_API_KEY="zSTy6et5Rw0Dzmv19dCnDz5R6s6Zx4G5"

echo "API keys set. Starting FastAPI server..."
uvicorn main:app --reload 