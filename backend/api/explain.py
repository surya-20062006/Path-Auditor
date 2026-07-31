from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.postgres import get_db
from backend.models.schema import DecisionSummary, DecisionSummarySchema, User
from backend.auth.jwt import get_current_user, require_auditor_or_admin
from audit.summarizer import summarizer_generator

router = APIRouter(tags=["Decision Explanations & Summaries"])


class SummarizeRequest(BaseModel):
    run_id: str = Field(..., description="UUID of the agent run to summarize")


class RegulatoryChallengeRequest(BaseModel):
    session_id: str = Field(..., description="Audit Session ID to generate challenge response for")


@router.post("/summarize", response_model=DecisionSummarySchema)
def get_or_create_plain_english_summary(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns existing or generates new Plain English Customer-Readable Decision Summary
    explaining why decision happened without technical jargon.
    """
    existing_summary = (
        db.query(DecisionSummary)
        .filter(DecisionSummary.run_id == request.run_id)
        .first()
    )
    if not existing_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audit record or decision summary found for this run_id."
        )
    return existing_summary


@router.post("/audit/regulatory-explanation", response_model=Dict[str, Any])
def generate_challenge_response_document(
    request: RegulatoryChallengeRequest,
    current_user: User = Depends(require_auditor_or_admin),
    db: Session = Depends(get_db)
):
    """
    Challenge Response Generator (BONUS):
    Produces a formal regulatory compliance explanation document answering:
    - Why loan was rejected or approved
    - Which evidence was considered
    - What rules were applied
    - What data sources were used
    """
    doc_json = summarizer_generator.generate_regulatory_challenge_explanation(db, session_id=request.session_id)
    if not doc_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session ID not found or no agent runs available."
        )
    return doc_json
