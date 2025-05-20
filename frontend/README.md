# Legal Assistant Frontend

This Next.js application provides a frontend for a legal assistant chatbot with AI integration.

## AI Chat Integration

### Setup Instructions

1. Create a `.env.local` file in the frontend directory with the following content:
```
# OpenAI API key - Required for AI integration
OPENAI_API_KEY=your_openai_api_key_here

# Backend API URL - Change this if your backend is running on a different URL
BACKEND_URL=http://localhost:8000
```

2. Replace `your_openai_api_key_here` with your actual OpenAI API key.

3. Start the development server:
```
cd frontend
npm run dev
```

4. Make sure your backend server is also running:
```
cd backend
python main.py
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser to use the chatbot.

### How It Works

1. User messages are sent to the Next.js API route
2. The API route forwards the query to the backend server
3. The backend extracts legal entities and searches relevant information
4. The OpenAI API processes this information to provide a coherent response
5. The response is returned to the frontend and displayed to the user

### Features

- Real-time chat interface
- Legal entity extraction
- Integration with Indian Kanoon database
- AI-powered coherent responses
