# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from legal_ner import load_model, extract_ner_entities
import json
import os
import logging

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
    # "your-vercel-app-url.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize IK API when FastAPI starts ---
IK_API_KEY = "18a7742b111567c20f1f9d59e124e61f8740eab2"
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

class ChatQuery(BaseModel):
    query: str

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
        
        # Build response
        overall_message = {
            "user_query": user_query,
            "extracted_legal_entities": extracted_entities,
            "indian_kanoon_results": indian_kanoon_results,
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