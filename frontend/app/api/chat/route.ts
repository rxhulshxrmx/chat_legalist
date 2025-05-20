// app/api/chat/route.ts
import { NextRequest } from "next/server";
import { Message } from "ai";

// Get the backend URL from environment variables or use localhost as fallback
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  try {
    // Parse request body
    const body = await req.json();
    
    if (!body.messages) {
      return Response.json({ error: "No messages provided" }, { status: 400 });
    }

    // Get the last user message
    const lastUserMessage = body.messages[body.messages.length - 1];
    const query = lastUserMessage.content;

    // Call backend API
    const backendResponse = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    // Get the raw backend data
    const backendData = await backendResponse.json();
    
    // Format response for display
    let responseText = "";
    
    if (backendData.response) {
      const lawyerResponse = backendData.response.lawyer_response;
      
      // If we have a lawyer response from Gemini, use that
      if (lawyerResponse) {
        responseText = lawyerResponse;
      } else {
        // Fallback to raw data format if no lawyer response
        const entities = backendData.response.extracted_legal_entities || [];
        const iKResults = backendData.response.indian_kanoon_results || {};
        
        responseText = `Query: ${query}\n\n`;
        
        if (entities.length > 0) {
          responseText += `Entities: ${entities.join(', ')}\n\n`;
        }
        
        responseText += `Results: ${JSON.stringify(iKResults, null, 2)}`;
      }
    } else {
      responseText = JSON.stringify(backendData);
    }
    
    // Return a correctly formatted response for the frontend
    const message: Message = {
      id: Date.now().toString(),
      role: "assistant",
      content: responseText,
      createdAt: new Date()
    };

    return new Response(JSON.stringify(message));
    
  } catch (error) {
    console.error("Error:", error);
    
    // Return error in compatible format
    const errorMessage: Message = {
      id: Date.now().toString(),
      role: "assistant",
      content: "Error processing request",
      createdAt: new Date()
    };
    
    return new Response(JSON.stringify(errorMessage), { status: 200 });
  }
}

// Add OPTIONS handler for CORS
export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
  });
}