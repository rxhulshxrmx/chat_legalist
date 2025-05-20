import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    // Get current model preference from backend
    const response = await fetch(`${BACKEND_URL}/get-model-preference`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error fetching model preference:", error);
    return Response.json(
      { error: "Failed to fetch model preference", model: "mistral" },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    if (!body.model || !["mistral", "gemini"].includes(body.model)) {
      return Response.json(
        { error: "Invalid model specified. Must be 'mistral' or 'gemini'" },
        { status: 400 }
      );
    }

    // Set model preference on backend
    const response = await fetch(`${BACKEND_URL}/set-model-preference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: body.model }),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error("Error setting model preference:", error);
    return Response.json(
      { error: "Failed to set model preference" },
      { status: 500 }
    );
  }
} 