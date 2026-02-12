from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import logging
from assessment import AssessmentManager, SymptomAssessment, AssessmentStep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessment", tags=["assessment"])

# Session storage (in production, use Redis or database)
assessment_sessions: Dict[str, SymptomAssessment] = {}

class AssessmentRequest(BaseModel):
    session_id: Optional[str] = None
    response: Optional[str] = None
    action: str = "start"  # start, respond, reset

class AssessmentResponse(BaseModel):
    session_id: str
    question: Optional[str] = None
    type: str
    step: str
    examples: Optional[list] = None
    assessment: Optional[dict] = None
    is_complete: bool = False

@router.post("/start", response_model=AssessmentResponse)
async def start_assessment():
    """Start a new symptom assessment session."""
    session_id = str(uuid.uuid4())
    
    # Create new assessment
    assessment = SymptomAssessment(step=AssessmentStep.SYMPTOM)
    assessment_sessions[session_id] = assessment
    
    # Get first question
    manager = AssessmentManager()
    next_question = manager.get_next_question(session_id, assessment)
    
    logger.info(f"Started new assessment session: {session_id}")
    
    return AssessmentResponse(
        session_id=session_id,
        question=next_question["question"],
        type=next_question["type"],
        step=next_question["step"],
        examples=next_question.get("examples"),
        is_complete=False
    )

@router.post("/respond", response_model=AssessmentResponse)
async def respond_to_assessment(request: AssessmentRequest):
    """Process user response and get next question or summary."""
    
    if not request.session_id or request.session_id not in assessment_sessions:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    
    if not request.response:
        raise HTTPException(status_code=400, detail="Response is required")
    
    session_id = request.session_id
    assessment = assessment_sessions[session_id]
    
    # Process response
    manager = AssessmentManager()
    updated_assessment = manager.process_response(session_id, request.response, assessment)
    
    # Get next question or summary
    next_step = manager.get_next_question(session_id, updated_assessment)
    
    # Check if assessment is complete
    is_complete = updated_assessment.step == AssessmentStep.COMPLETE
    
    if is_complete:
        logger.info(f"Completed assessment session: {session_id}")
        return AssessmentResponse(
            session_id=session_id,
            question=None,
            type="summary",
            step="complete",
            assessment=next_step.get("assessment"),
            is_complete=True
        )
    else:
        return AssessmentResponse(
            session_id=session_id,
            question=next_step["question"],
            type=next_step["type"],
            step=next_step["step"],
            examples=next_step.get("examples"),
            is_complete=False
        )

@router.get("/session/{session_id}")
async def get_assessment_session(session_id: str):
    """Get current assessment session status."""
    
    if session_id not in assessment_sessions:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    
    assessment = assessment_sessions[session_id]
    
    return {
        "session_id": session_id,
        "current_step": assessment.step,
        "primary_symptom": assessment.primary_symptom,
        "duration": assessment.duration,
        "severity": assessment.severity,
        "additional_symptoms": assessment.additional_symptoms,
        "is_complete": assessment.step == AssessmentStep.COMPLETE
    }

@router.post("/reset")
async def reset_assessment(request: AssessmentRequest):
    """Reset or continue an assessment session."""
    
    if request.action == "reset" and request.session_id:
        # Remove existing session
        if request.session_id in assessment_sessions:
            del assessment_sessions[request.session_id]
            logger.info(f"Reset assessment session: {request.session_id}")
    
    # Start new assessment
    return await start_assessment()

@router.delete("/session/{session_id}")
async def delete_assessment_session(session_id: str):
    """Delete an assessment session."""
    
    if session_id not in assessment_sessions:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    
    del assessment_sessions[session_id]
    logger.info(f"Deleted assessment session: {session_id}")
    
    return {"message": "Assessment session deleted successfully"}

@router.get("/sessions")
async def list_assessment_sessions():
    """List all active assessment sessions."""
    
    sessions = []
    for session_id, assessment in assessment_sessions.items():
        sessions.append({
            "session_id": session_id,
            "current_step": assessment.step,
            "primary_symptom": assessment.primary_symptom,
            "is_complete": assessment.step == AssessmentStep.COMPLETE
        })
    
    return {"sessions": sessions, "total": len(sessions)}
