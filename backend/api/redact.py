from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database.postgres import get_db
from backend.models.schema import User, PIIRedaction, PIIRedactionSchema
from backend.auth.jwt import get_current_user, require_auditor_or_admin
from audit.redactor import pii_redactor
from backend.core.logger import logger

router = APIRouter(tags=["PII Detection & Redaction"])


class RedactRequest(BaseModel):
    text: str = Field(..., description="Text containing sensitive PII to scan and redact")
    field_path: str = Field(default="input_text", description="Field identifier")


class RedactResponse(BaseModel):
    redacted_text: str
    redactions: List[Dict[str, Any]]
    total_redactions: int


class UnredactRequest(BaseModel):
    encrypted_token: str = Field(..., description="Base64 encoded AES-256-GCM token to decrypt")


class UnredactResponse(BaseModel):
    plaintext_value: str
    status: str = "decrypted"


@router.post("/redact", response_model=RedactResponse)
def scan_and_redact_pii(
    request: RedactRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Scan text for sensitive PII (PAN, SSN, Aadhaar, Email, Phone, Credit Card, Passport, etc.),
    replace tokens with <REDACTED_ENTITY>, and return encrypted original references.
    """
    redacted, items = pii_redactor.redact_text(request.text, field_path=request.field_path)
    return RedactResponse(
        redacted_text=redacted,
        redactions=items,
        total_redactions=len(items)
    )


@router.post("/unredact", response_model=UnredactResponse)
def decrypt_pii_token(
    request: UnredactRequest,
    current_user: User = Depends(require_auditor_or_admin)
):
    """
    Secure PII inspection endpoint:
    Decrypt AES-256-GCM token back to original PII plaintext.
    Restricted to Admin and Auditor roles only.
    """
    try:
        decrypted = pii_redactor.decrypt_token(request.encrypted_token)
        logger.info(
            "PII token decrypted by auditor",
            user_id=current_user.id,
            role=current_user.role
        )
        return UnredactResponse(plaintext_value=decrypted)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decrypt token. Unauthorized key or corrupted AES payload."
        )
