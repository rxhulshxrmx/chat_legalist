# Legal Assistant Frontend

This Next.js application provides a frontend for a legal assistant chatbot with AI integration.

## Setup Instructions

1. Create a `.env.local` file in the frontend directory with the following content:
```
# Backend API URL - Change this if your backend is running on a different URL
BACKEND_URL=http://localhost:8000
```

2. Start the development server:
```
cd frontend
npm run dev
```

3. Make sure your backend server is also running:
```
cd backend
python main.py
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to use the chatbot.

### Features

- Real-time chat interface
- Legal entity extraction
- Integration with Indian Kanoon database
- AI-powered coherent responses
