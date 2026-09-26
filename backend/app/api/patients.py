from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.audit_service import log_action

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[PatientResponse])
def list_patients(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Patient)
    if search:
        s = f"%{search}%"
        query = query.filter((Patient.full_name.ilike(s)) | (Patient.patient_code.ilike(s)))
    
    patients = query.order_by(Patient.created_at.desc()).all()
    
    res = []
    for p in patients:
        active_wounds = db.query(WoundCase).filter(WoundCase.patient_id == p.id, WoundCase.status == "Active").count()
        p_dict = PatientResponse.model_validate(p)
        p_dict.active_wounds_count = active_wounds
        res.append(p_dict)
    return res

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Clinician"))
):
    # Auto-generate next synthetic Patient ID e.g. PAT-1004
    count = db.query(Patient).count() + 1001
    code = f"PAT-{count}"

    p = Patient(
        patient_code=code,
        full_name=patient_in.full_name,
        age=patient_in.age,
        gender=patient_in.gender,
        medical_notes=patient_in.medical_notes
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    log_action(db, user_id=current_user.id, action="patient_create",
               target_type="Patient", target_id=str(p.id),
               details=f"Created patient {p.patient_code}")
    res = PatientResponse.model_validate(p)
    res.active_wounds_count = 0
    return res

@router.get("/{id}", response_model=PatientResponse)
def get_patient(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Patient).filter(Patient.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    active_wounds = db.query(WoundCase).filter(WoundCase.patient_id == p.id, WoundCase.status == "Active").count()
    res = PatientResponse.model_validate(p)
    res.active_wounds_count = active_wounds
    return res

@router.put("/{id}", response_model=PatientResponse)
def update_patient(
    id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Clinician"))
):
    p = db.query(Patient).filter(Patient.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    for field, value in patient_in.model_dump(exclude_unset=True).items():
        setattr(p, field, value)

    db.commit()
    db.refresh(p)

    log_action(db, user_id=current_user.id, action="patient_update",
               target_type="Patient", target_id=str(p.id),
               details=f"Updated patient {p.patient_code}")

    active_wounds = db.query(WoundCase).filter(WoundCase.patient_id == p.id, WoundCase.status == "Active").count()
    res = PatientResponse.model_validate(p)
    res.active_wounds_count = active_wounds
    return res

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    p = db.query(Patient).filter(Patient.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    log_action(db, user_id=current_user.id, action="patient_delete",
               target_type="Patient", target_id=str(p.id),
               details=f"Deleted patient {p.patient_code}")
    db.delete(p)
    db.commit()
    return None
