"""
legalEaseAPI/routes.py

Defines the /generate endpoint that the Streamlit frontend calls.
Validates the incoming payload with Pydantic, delegates text
generation to GeminiDocumentGenerator, and returns structured JSON.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_core.gemini_generator import (
    GeminiDocumentGenerator,
    GeminiConfigurationError,
    GeminiGenerationError,
)

logger = logging.getLogger("legalease.routes")

router = APIRouter()

# The generator is created lazily so that importing this module doesn't
# fail just because GEMINI_API_KEY hasn't been set yet (e.g. during tests
# that only check routing, or when running `uvicorn --reload` before the
# .env file exists).
_generator = None


def get_generator() -> GeminiDocumentGenerator:
    global _generator
    if _generator is None:
        _generator = GeminiDocumentGenerator()
    return _generator


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=1, description="E.g. 'Employment Contract', 'NDA'")
    parties: str = Field(..., min_length=1, description="Names/roles of parties involved")
    terms: str = Field(..., min_length=1, description="Semicolon-separated terms/clauses")
    dates: str = Field(..., min_length=1, description="Effective date of the document")


class DocumentResponse(BaseModel):
    document: str


@router.get("/health")
def health_check():
    """Simple liveness check used by deployment platforms and local testing."""
    return {"status": "ok"}


@router.post("/generate", response_model=DocumentResponse)
def generate_legal_document(request: DocumentRequest):
    """
    Accepts document details and returns AI-generated legal document text.
    """
    try:
        generator = get_generator()
    except GeminiConfigurationError as exc:
        logger.error("Gemini configuration error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        document_text = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            dates=request.dates,
        )
    except GeminiGenerationError as exc:
        logger.error("Gemini generation error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return DocumentResponse(document=document_text)