from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class WoundCaseCreate(BaseModel):
    patient_id: int
    location: str # Left lower leg, Right foot, Forearm, Heel
    wound_type: str # Venous Ulcer, Diabetic Foot Ulcer, Pressure Injury, Surgical
    status: Optional[str] = "Active"
    notes: Optional[str] = None

class WoundCaseUpdate(BaseModel):
    location: Optional[str] = None
    wound_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class WoundCaseResponse(BaseModel):
    id: int
    case_code: str
    patient_id: int
    patient_code: Optional[str] = None
    patient_name: Optional[str] = None
    location: str
    wound_type: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    latest_area_mm2: Optional[float] = None
    latest_visit_date: Optional[datetime] = None
    healing_status: Optional[str] = "Baseline"
    visits_count: Optional[int] = 0

    class Config:
        from_attributes = True
