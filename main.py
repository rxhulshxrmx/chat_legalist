# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from legal_ner import load_model, extract_ner_entities
import requests
import json
from ik_download import IKApi, FileStorage
import os
import argparse
from fastapi import HTTPException

app = FastAPI()

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
os.makedirs(STORAGE_DIR, exist_ok=True)
file_storage = FileStorage(STORAGE_DIR)
ik_api = IKApi(argparse.Namespace(
    token=IK_API_KEY,
    datadir=STORAGE_DIR,
    maxpages=1,
    maxcites=0,
    maxcitedby=0,
    orig=False,
    pathbysrc=False,
    numworkers=5,
    addedtoday=False,
    fromdate=None,
    todate=None,
    sortby=None
), file_storage)

# --- Load NER model when FastAPI starts ---
model, tokenizer = load_model()

class ChatQuery(BaseModel):
    query: str

@app.post("/chat/")
async def chat(chat_query: ChatQuery):
    user_query = chat_query.query
    print(f"User query: {user_query}")

    entities = extract_ner_entities(user_query, model, tokenizer)
    extracted_entities = [ent[0] for ent in entities if ent[1] != 'O']
    print(f"Extracted entities: {extracted_entities}")

    indian_kanoon_results = None
    if extracted_entities:
        search_query = " ".join(extracted_entities)
        print(f"Searching Indian Kanoon for: {search_query}")
        results_str = ik_api.search(search_query, pagenum=0, maxpages=1)
        try:
            indian_kanoon_results = json.loads(results_str)
            print("Indian Kanoon API Results:", indian_kanoon_results)
        except json.JSONDecodeError:
            print("Error decoding Indian Kanoon JSON response.")
            indian_kanoon_results = {"error": "Failed to decode Indian Kanoon response."}
    else:
        indian_kanoon_results = {"message": "No relevant entities found to search Indian Kanoon."}

    overall_message = {
        "user_query": user_query,
        "extracted_legal_entities": extracted_entities,
        "indian_kanoon_results": indian_kanoon_results,
    }

    return {"response": overall_message}

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)