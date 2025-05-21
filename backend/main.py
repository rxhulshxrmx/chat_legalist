# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from legal_ner import load_model, extract_ner_entities
import json
import os
import logging
import google.generativeai as genai
from mistralai import Mistral
from dotenv import load_dotenv

# Import the IKApi and FileStorage from the module
# Make sure your file is named ik_download.py and accessible in the path
from ik_download import IKApi, FileStorage, get_arg_parser

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your production domains here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# --- Initialize Google Gemini API ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Successfully initialized Google Gemini API")
else:
    logger.warning("GEMINI_API_KEY not found. Gemini features will be disabled.")

# --- Initialize Mistral AI API ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
mistral_client = None
if MISTRAL_API_KEY:
    mistral_client = Mistral(api_key=MISTRAL_API_KEY)
    logger.info("Successfully initialized Mistral AI API")
else:
    logger.warning("MISTRAL_API_KEY not found. Mistral AI features will be disabled.")

# --- Initialize IK API when FastAPI starts ---
IK_API_KEY = os.environ.get("IK_API_KEY", "") # Get from environment variables
STORAGE_DIR = "./indian_kanoon_cache"

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_DIR, exist_ok=True)

# Default args for uvicorn run
class DummyArgs:
    token = IK_API_KEY
    datadir = STORAGE_DIR
    maxpages = 1
    maxcites = 0
    maxcitedby = 0
    orig = False
    pathbysrc = False
    numworkers = 5
    addedtoday = False
    fromdate = None
    todate = None
    sortby = None

try:
    file_storage = FileStorage(STORAGE_DIR)
    # Use DummyArgs by default
    ik_api = IKApi(DummyArgs(), file_storage)
    logger.info("Successfully initialized Indian Kanoon API")
except Exception as e:
    logger.error(f"Failed to initialize Indian Kanoon API: {str(e)}")
    raise

# --- Load NER model when FastAPI starts ---
try:
    model, tokenizer = load_model()
    logger.info("Successfully loaded NER model")
except Exception as e:
    logger.error(f"Failed to load NER model: {str(e)}")
    raise

# Default model preference (can be "mistral" or "gemini")
MODEL_PREFERENCE = "mistral"

class ChatQuery(BaseModel):
    query: str

class ModelPreference(BaseModel):
    model: str  # "mistral" or "gemini"

@app.post("/set-model-preference")
async def set_model_preference(preference: ModelPreference):
    """Set the preferred AI model to use for responses."""
    global MODEL_PREFERENCE
    
    if preference.model not in ["mistral", "gemini"]:
        raise HTTPException(status_code=400, detail="Invalid model preference. Must be 'mistral' or 'gemini'")
    
    MODEL_PREFERENCE = preference.model
    logger.info(f"Model preference set to: {MODEL_PREFERENCE}")
    
    return {"message": f"Model preference set to {MODEL_PREFERENCE}"}

@app.get("/get-model-preference")
async def get_model_preference():
    """Get the current preferred AI model."""
    return {"model": MODEL_PREFERENCE}

# Function to get Gemini response using legal context
async def get_gemini_response(user_query, legal_entities, indian_kanoon_results):
    try:
        if not GEMINI_API_KEY:
            return {"gemini_response": "Gemini API key not configured. Please set the GEMINI_API_KEY environment variable."}
        
        # Create a prompt for Gemini with legal context
        prompt = f"""
        You are an experienced lawyer specializing in Indian law. Your task is to provide a clear, helpful response to a legal question.

        USER QUERY: {user_query}

        LEGAL ENTITIES IDENTIFIED: {', '.join(legal_entities) if legal_entities else "None"}

        INDIAN KANOON (LEGAL DATABASE) SEARCH RESULTS: 
        {json.dumps(indian_kanoon_results, indent=2)}

        RESPONSE REQUIREMENTS:
        1. Be concise and to the point
        2. Use short, clear paragraphs with proper spacing
        3. Focus on the most relevant legal information
        4. Avoid unnecessary legal jargon
        5. Format your response with clear headings if appropriate
        6. Provide a brief summary at the beginning
        7. Do not include disclaimers or introductions like "Based on..." or "According to..."
        8. Use numbered lists or bullet points when listing multiple items
        """
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        return {"gemini_response": response.text}
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        return {"gemini_response": f"Error generating response: {str(e)}"}

# Function to get Mistral AI response using legal context
async def get_mistral_response(user_query, legal_entities, indian_kanoon_results):
    try:
        if not mistral_client:
            return {"response": "Mistral API key not configured. Please set the MISTRAL_API_KEY environment variable."}
        
        # Create a prompt for Mistral with legal context
        prompt = f"""
        You are an experienced lawyer specializing in Indian law. Your task is to provide a clear, helpful response to a legal question.

        USER QUERY: {user_query}

        LEGAL ENTITIES IDENTIFIED: {', '.join(legal_entities) if legal_entities else "None"}

        INDIAN KANOON (LEGAL DATABASE) SEARCH RESULTS: 
        {json.dumps(indian_kanoon_results, indent=2)}

        RESPONSE REQUIREMENTS:
        1. Be concise and to the point
        2. Use short, clear paragraphs with proper spacing
        3. Focus on the most relevant legal information
        4. Avoid unnecessary legal jargon
        5. Format your response with clear headings if appropriate
        6. Provide a brief summary at the beginning
        7. Do not include disclaimers or introductions like "Based on..." or "According to..."
        8. Use numbered lists or bullet points when listing multiple items
        """
        
        # Call Mistral AI API
        chat_response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return {"response": chat_response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error calling Mistral AI API: {str(e)}")
        return {"response": f"Error generating response: {str(e)}"}

@app.post("/chat")
@app.post("/chat/")
async def chat(chat_query: ChatQuery):
    user_query = chat_query.query
    logger.info(f"User query: {user_query}")
    
    try:
        # Extract named entities
        entities = extract_ner_entities(user_query, model, tokenizer)
        extracted_entities = [ent[0] for ent in entities if ent[1] != 'O']
        logger.info(f"Extracted entities: {extracted_entities}")
        
        # Search Indian Kanoon if we have entities
        if extracted_entities:
            search_query = " ".join(extracted_entities)
            logger.info(f"Searching Indian Kanoon for: {search_query}")
            
            try:
                results_str = ik_api.search(search_query, pagenum=0, maxpages=1)
                indian_kanoon_results = json.loads(results_str)
                logger.info("Successfully retrieved Indian Kanoon results")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding Indian Kanoon JSON response: {str(e)}")
                indian_kanoon_results = {"error": "Failed to decode Indian Kanoon response."}
            except Exception as e:
                logger.error(f"Error querying Indian Kanoon API: {str(e)}")
                indian_kanoon_results = {"error": f"Error querying Indian Kanoon: {str(e)}"}
        else:
            logger.info("No relevant entities found to search Indian Kanoon")
            indian_kanoon_results = {"message": "No relevant entities found to search Indian Kanoon."}
        
        # Use the preferred model (with fallbacks)
        lawyer_response = None
        model_used = None
        
        if MODEL_PREFERENCE == "mistral" and mistral_client:
            logger.info("Using Mistral AI for response generation")
            ai_response = await get_mistral_response(user_query, extracted_entities, indian_kanoon_results)
            lawyer_response = ai_response["response"]
            model_used = "mistral"
        elif MODEL_PREFERENCE == "gemini" and GEMINI_API_KEY:
            logger.info("Using Google Gemini for response generation")
            gemini_response = await get_gemini_response(user_query, extracted_entities, indian_kanoon_results)
            lawyer_response = gemini_response["gemini_response"]
            model_used = "gemini"
        # Fallback options if preferred model isn't available
        elif mistral_client:
            logger.info("Preferred model not available, falling back to Mistral AI")
            ai_response = await get_mistral_response(user_query, extracted_entities, indian_kanoon_results)
            lawyer_response = ai_response["response"]
            model_used = "mistral"
        elif GEMINI_API_KEY:
            logger.info("Preferred model not available, falling back to Google Gemini")
            gemini_response = await get_gemini_response(user_query, extracted_entities, indian_kanoon_results)
            lawyer_response = gemini_response["gemini_response"]
            model_used = "gemini"
        else:
            logger.warning("No AI service available")
            lawyer_response = "No AI service is configured. Please set either MISTRAL_API_KEY or GEMINI_API_KEY."
            model_used = "none"
        
        # Build response with all information
        overall_message = {
            "user_query": user_query,
            "extracted_legal_entities": extracted_entities,
            "indian_kanoon_results": indian_kanoon_results,
            "lawyer_response": lawyer_response,
            "model_used": model_used
        }
        
        return {"response": overall_message}
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Legal Assistant API is running!"}

if __name__ == "__main__":
    import argparse
    import uvicorn
    parser = get_arg_parser()
    args = parser.parse_args()
    file_storage = FileStorage(args.datadir)
    ik_api = IKApi(args, file_storage)
    uvicorn.run(app, host="0.0.0.0", port=8000)