#!/bin/bash

# Kill any running uvicorn processes
pkill -f 'uvicorn main:app'

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "Environment loaded. Starting FastAPI server..."
uvicorn main:app --reload 