from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class PatientCreate(BaseModel):
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_notes: Optional[str] = None

class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_notes: Optional[str] = None
    is_archived: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    patient_code: str
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_notes: Optional[str] = None
    is_archived: str
    created_at: datetime
    updated_at: datetime
    active_wounds_count: Optional[int] = 0

    class Config:
        from_attributes = True
