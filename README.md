# Legal Assistant Project

A full-stack application for legal information retrieval and assistance.

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── main.py       # Main application file
│   ├── legal_ner.py  # Legal NER implementation
│   ├── ik_download.py # Indian Kanoon API integration
│   └── requirements.txt
│
└── frontend/         # Next.js frontend
    ├── app/         # Next.js app directory
    ├── public/      # Static files
    └── package.json # Frontend dependencies
```

## Setup

### Backend Setup
1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend:
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the frontend:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Development

- Backend API documentation: `http://localhost:8000/docs`
- Frontend development server: `http://localhost:3000`

## Deployment

The project is structured to be easily deployable:
- Backend can be deployed to any Python-compatible hosting (e.g., Heroku, DigitalOcean)
- Frontend can be deployed to Vercel or similar platforms

## Environment Variables

### Backend
- `IK_API_KEY`: Your Indian Kanoon API key

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

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