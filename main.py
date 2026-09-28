"""
legalEaseAPI/main.py

FastAPI application entry point for LegalEase.
Run with:  uvicorn legalEaseAPI.main:app --reload
"""

import logging
import sys
import os

# Allow `python legalEaseAPI/main.py` to work even though this module
# uses absolute imports like `ai_core.gemini_generator` and `config`.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from legalEaseAPI.routes import router
from config import APP_TITLE, BACKEND_HOST, BACKEND_PORT

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=APP_TITLE)

# Allow the Streamlit frontend (different port) to call this API locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": f"Welcome to {APP_TITLE} API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("legalEaseAPI.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)