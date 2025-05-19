# Legal Information Backend

A FastAPI-based backend service for retrieving and managing legal information from Indian Kanoon.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To run the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

- `POST /chat/`: Process legal queries and return relevant information
  - Request body: `{"query": "your legal question here"}`
  - Returns processed legal information and relevant case references

## Project Structure

- `api/`: API endpoints and route handlers
- `database/`: Database models and connection logic
- `search/`: Semantic search implementation
- `models/`: Data models and schemas
- `main.py`: Application entry point 