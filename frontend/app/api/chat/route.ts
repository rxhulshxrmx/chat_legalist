// app/api/chat/route.ts
import { google } from '@ai-sdk/google';
import { streamText } from "ai";

// Get the backend URL from environment variables or use localhost as fallback
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// Enable CORS
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
};

// Helper function to create a streaming response
function createStreamResponse(content: string) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      // Send the content as a single chunk
      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({
          id: Date.now().toString(),
          role: 'assistant',
          content: content,
        })}\n\n`)
      );
      
      // Signal the end of the stream
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      ...corsHeaders,
      'Content-Type': 'text/event-stream',
    },
  });
}

// Helper function to create error response
function createErrorResponse(error: unknown, status = 500) {
  const message = error instanceof Error ? error.message : 'An unknown error occurred';
  console.error('Error:', message, error);
  
  return new Response(
    JSON.stringify({ error: message }),
    {
      status,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

export async function POST(req: Request) {
  console.log('Received request at:', new Date().toISOString());
  
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders,
    });
  }
  
  // Log request headers for debugging
  console.log('Request headers:', Object.fromEntries(req.headers.entries()));
  
  try {
    // 1. Parse the request body
    let messages;
    try {
      const body = await req.json();
      messages = body.messages;
      if (!Array.isArray(messages)) {
        throw new Error('Invalid messages format');
      }
      console.log('Parsed messages:', JSON.stringify(messages, null, 2));
    } catch (error) {
      console.error('Error parsing request body:', error);
      return createErrorResponse('Invalid request body', 400);
    }

    // 2. Get the last user message
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage || typeof lastMessage.content !== 'string') {
      return createErrorResponse('Invalid message format', 400);
    }
    const userMessage = lastMessage.content;
    console.log('User message:', userMessage);

    // 3. Call the FastAPI backend
    let backendResponse;
    try {
      console.log('Calling backend API with message:', userMessage);
      const startTime = Date.now();
      
      console.log('Using backend URL:', `${BACKEND_URL}/chat`);
      backendResponse = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage }),
      });
      
      const responseTime = Date.now() - startTime;
      console.log(`Backend response received in ${responseTime}ms, status:`, backendResponse.status);
      
      if (!backendResponse.ok) {
        const errorText = await backendResponse.text().catch(() => 'No error details');
        console.error('Backend error response:', backendResponse.status, errorText);
        return createErrorResponse(`Legal service error: ${errorText}`, backendResponse.status);
      }
    } catch (error) {
      console.error('Failed to fetch from backend:', error);
      return createErrorResponse('Failed to connect to the legal service');
    }

    // 4. Parse backend response
    let backendData;
    try {
      console.log('Parsing backend response...');
      const startParseTime = Date.now();
      backendData = await backendResponse.json();
      console.log(`Backend data parsed in ${Date.now() - startParseTime}ms`);
      
      // Log a preview of the response (first 500 chars to avoid logging too much)
      const preview = JSON.stringify(backendData).substring(0, 500);
      console.log('Backend data preview:', preview);
    } catch (error) {
      console.error('Error parsing backend response:', error);
      const responseText = await backendResponse.text().catch(() => 'Could not get response text');
      console.error('Raw backend response:', responseText);
      return createErrorResponse('Invalid response from legal service');
    }

    // 6. Prepare messages for Gemini
    const backendResponseText = typeof backendData.response === 'string' 
      ? backendData.response 
      : JSON.stringify(backendData.response, null, 2);
    
    const allMessages = [
      ...messages,
      {
        role: 'user' as const,
        content: `Legal information: ${backendResponseText}`
      }
    ];

    // 7. Call Gemini
    console.log('Calling Gemini with messages:', JSON.stringify(allMessages, null, 2));
    try {
      const geminiStartTime = Date.now();
      
      // Call Gemini with streaming
      const result = await streamText({
        model: google('gemini-2.0-flash'),
        system: `You are a legal AI assistant. Analyze the provided legal information and provide a clear, 
        concise response. Focus on the key points and make the information easy to understand.`,
        messages: allMessages,
      });

      console.log(`Gemini API call completed in ${Date.now() - geminiStartTime}ms`);
      
      // Get the full text from the result
      const fullText = await result.text;
      console.log(`Got Gemini response (${fullText.length} chars)`);
      
      // Return the response as a stream
      return createStreamResponse(fullText);
      
    } catch (error) {
      console.error('Error calling Gemini:', error);
      return createErrorResponse('Failed to generate response');
    }
    
  } catch (error) {
    console.error('Unexpected error in chat API:', error);
    // Ensure we're returning a proper Response object
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'An unknown error occurred',
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
}

// Add CORS headers to all responses
export const OPTIONS = async () => {
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
};