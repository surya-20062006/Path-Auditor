from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.postgres import get_db
from backend.models.schema import AgentRun, AgentRunDetailSchema, User, RiskLevel
from backend.auth.jwt import get_current_user, require_auditor_or_admin
from audit.reconstructor import reconstructor

router = APIRouter(prefix="/audit", tags=["Audit & Decision Path Reconstructor"])


@router.get("/session/{session_id}", response_model=Dict[str, Any])
def get_session_decision_path_timeline(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decision Path Reconstructor:
    Returns complete causal chain timeline:
    User Input -> Retrieved Context -> Tool Calls -> Reasoning -> Decision -> Final Output.
    """
    timeline_json = reconstructor.reconstruct_session_timeline(db, session_id=session_id)
    if not timeline_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session ID not found in audit records."
        )

    # Customers can only view their own sessions; Admin/Auditor/Developer can view all
    if current_user.role == "customer" and timeline_json.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to view your own audit session timelines."
        )

    return timeline_json


@router.get("/user/{user_id}", response_model=List[AgentRunDetailSchema])
def get_user_agent_runs_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all audited agent runs executed by a specific user.
    """
    if current_user.role == "customer" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers can only inspect their own agent run histories."
        )

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.user_id == user_id)
        .order_by(AgentRun.start_time.desc())
        .limit(limit)
        .all()
    )
    return runs


@router.get("/search", response_model=List[AgentRunDetailSchema])
def search_agent_runs(
    session_id: Optional[str] = Query(None, description="Filter by Session UUID"),
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    risk_level: Optional[RiskLevel] = Query(None, description="low | medium | high | critical"),
    model_name: Optional[str] = Query(None, description="Filter by AI model"),
    status_code: Optional[str] = Query(None, alias="status", description="success | error"),
    query_text: Optional[str] = Query(None, description="Keyword search in input or output text"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enterprise multi-filter audit search.
    Search by Session, User, Risk Score, Decision Type, Model, and keyword search.
    """
    query = db.query(AgentRun)

    if current_user.role == "customer":
        query = query.filter(AgentRun.user_id == current_user.id)
    elif user_id:
        query = query.filter(AgentRun.user_id == user_id)

    if session_id:
        query = query.filter(AgentRun.session_id == session_id)
    if risk_level:
        query = query.filter(AgentRun.risk_level == risk_level.value)
    if model_name:
        query = query.filter(AgentRun.model_name.ilike(f"%{model_name}%"))
    if status_code:
        query = query.filter(AgentRun.status == status_code)
    if query_text:
        query = query.filter(
            or_(
                AgentRun.input_text.ilike(f"%{query_text}%"),
                AgentRun.final_output.ilike(f"%{query_text}%")
            )
        )

    return query.order_by(AgentRun.start_time.desc()).limit(limit).all()
