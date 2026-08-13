from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, Measurement
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.ml.assistant import AIAssistantService

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post("/chat", response_model=AssistantResponse)
async def assistant_chat(
    req: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wound_history = []
    if req.wound_id:
        visits = db.query(Visit).filter(Visit.wound_id == req.wound_id).order_by(Visit.visit_number.asc()).all()
        for v in visits:
            meas = db.query(Measurement).filter(Measurement.visit_id == v.id).first()
            if meas:
                wound_history.append({
                    "visit_number": v.visit_number,
                    "visit_date": v.visit_date.isoformat(),
                    "area_mm2": meas.area_mm2,
                    "percentage_change": meas.percentage_change,
                    "healing_status": meas.healing_status
                })

    patient_info = None
    if req.patient_id:
        p = db.query(Patient).filter(Patient.id == req.patient_id).first()
        if p:
            w_count = db.query(WoundCase).filter(WoundCase.patient_id == p.id, WoundCase.status == "Active").count()
            patient_info = {
                "patient_code": p.patient_code,
                "full_name": p.full_name,
                "age": p.age,
                "gender": p.gender,
                "active_wounds_count": w_count
            }

    reply = await AIAssistantService.generate_response(
        prompt=req.message,
        wound_history=wound_history,
        patient_info=patient_info
    )

    return AssistantResponse(
        reply=reply,
        disclaimer="This assistant is a decision-support demonstration tool and does not provide diagnostic or medical opinions."
    )
