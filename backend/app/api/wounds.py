from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, Measurement, WoundImage, SegmentationResult
from app.schemas.wound import WoundCaseCreate, WoundCaseUpdate, WoundCaseResponse
from app.schemas.assessment import HealingHistoryPoint
from app.services.audit_service import log_action

router = APIRouter(prefix="/wounds", tags=["Wound Cases"])

@router.get("", response_model=List[WoundCaseResponse])
def list_wound_cases(
    patient_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WoundCase)
    if patient_id:
        query = query.filter(WoundCase.patient_id == patient_id)
    if status_filter:
        query = query.filter(WoundCase.status == status_filter)

    wounds = query.order_by(WoundCase.created_at.desc()).all()

    res = []
    for w in wounds:
        pat = db.query(Patient).filter(Patient.id == w.patient_id).first()
        v_count = db.query(Visit).filter(Visit.wound_id == w.id).count()

        latest_visit = db.query(Visit).filter(Visit.wound_id == w.id).order_by(Visit.visit_number.desc()).first()

        latest_area = None
        latest_date = None
        healing_st = "Baseline"

        if latest_visit:
            latest_date = latest_visit.visit_date
            meas = db.query(Measurement).filter(Measurement.visit_id == latest_visit.id).first()
            if meas:
                latest_area = meas.area_mm2
                healing_st = meas.healing_status

        item = WoundCaseResponse.model_validate(w)
        item.patient_code = pat.patient_code if pat else "N/A"
        item.patient_name = pat.full_name if pat else "N/A"
        item.latest_area_mm2 = latest_area
        item.latest_visit_date = latest_date
        item.healing_status = healing_st
        item.visits_count = v_count
        res.append(item)

    return res

@router.post("", response_model=WoundCaseResponse, status_code=status.HTTP_201_CREATED)
def create_wound_case(
    wound_in: WoundCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Clinician"))
):
    pat = db.query(Patient).filter(Patient.id == wound_in.patient_id).first()
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    count = db.query(WoundCase).count() + 1001
    code = f"WC-{count}"

    w = WoundCase(
        case_code=code,
        patient_id=wound_in.patient_id,
        location=wound_in.location,
        wound_type=wound_in.wound_type,
        status=wound_in.status or "Active",
        notes=wound_in.notes
    )
    db.add(w)
    db.commit()
    db.refresh(w)

    log_action(db, user_id=current_user.id, action="wound_create",
               target_type="WoundCase", target_id=str(w.id),
               details=f"Created wound case {w.case_code}")

    res = WoundCaseResponse.model_validate(w)
    res.patient_code = pat.patient_code
    res.patient_name = pat.full_name
    res.visits_count = 0
    return res

@router.get("/{id}", response_model=WoundCaseResponse)
def get_wound_case(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    w = db.query(WoundCase).filter(WoundCase.id == id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Wound case not found")

    pat = db.query(Patient).filter(Patient.id == w.patient_id).first()
    v_count = db.query(Visit).filter(Visit.wound_id == w.id).count()

    latest_visit = db.query(Visit).filter(Visit.wound_id == w.id).order_by(Visit.visit_number.desc()).first()

    latest_area = None
    latest_date = None
    healing_st = "Baseline"

    if latest_visit:
        latest_date = latest_visit.visit_date
        meas = db.query(Measurement).filter(Measurement.visit_id == latest_visit.id).first()
        if meas:
            latest_area = meas.area_mm2
            healing_st = meas.healing_status

    res = WoundCaseResponse.model_validate(w)
    res.patient_code = pat.patient_code if pat else "N/A"
    res.patient_name = pat.full_name if pat else "N/A"
    res.latest_area_mm2 = latest_area
    res.latest_visit_date = latest_date
    res.healing_status = healing_st
    res.visits_count = v_count
    return res

@router.put("/{id}", response_model=WoundCaseResponse)
def update_wound_case(
    id: int,
    wound_in: WoundCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Clinician"))
):
    w = db.query(WoundCase).filter(WoundCase.id == id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Wound case not found")

    for field, value in wound_in.model_dump(exclude_unset=True).items():
        setattr(w, field, value)

    db.commit()
    db.refresh(w)

    log_action(db, user_id=current_user.id, action="wound_update",
               target_type="WoundCase", target_id=str(w.id),
               details=f"Updated wound case {w.case_code}")

    pat = db.query(Patient).filter(Patient.id == w.patient_id).first()
    v_count = db.query(Visit).filter(Visit.wound_id == w.id).count()
    latest_visit = db.query(Visit).filter(Visit.wound_id == w.id).order_by(Visit.visit_number.desc()).first()
    latest_area = None
    latest_date = None
    healing_st = "Baseline"
    if latest_visit:
        latest_date = latest_visit.visit_date
        meas = db.query(Measurement).filter(Measurement.visit_id == latest_visit.id).first()
        if meas:
            latest_area = meas.area_mm2
            healing_st = meas.healing_status

    res = WoundCaseResponse.model_validate(w)
    res.patient_code = pat.patient_code if pat else "N/A"
    res.patient_name = pat.full_name if pat else "N/A"
    res.latest_area_mm2 = latest_area
    res.latest_visit_date = latest_date
    res.healing_status = healing_st
    res.visits_count = v_count
    return res

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wound_case(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin"))
):
    """
    Soft-delete equivalent: archives the wound case by setting status to 'Closed'
    rather than physically deleting the record. This preserves clinical history.
    A hard delete is intentionally not provided for healthcare safety.
    """
    w = db.query(WoundCase).filter(WoundCase.id == id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Wound case not found")

    # Soft-delete: mark as Closed instead of physical deletion
    w.status = "Closed"
    db.commit()
    db.refresh(w)

    log_action(db, user_id=current_user.id, action="wound_archive",
               target_type="WoundCase", target_id=str(w.id),
               details=f"Archived (closed) wound case {w.case_code}")
    return None

@router.get("/{id}/history", response_model=List[HealingHistoryPoint])
def get_wound_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    w = db.query(WoundCase).filter(WoundCase.id == id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Wound case not found")

    visits = db.query(Visit).filter(Visit.wound_id == id).order_by(Visit.visit_number.asc()).all()

    points = []
    for v in visits:
        meas = db.query(Measurement).filter(Measurement.visit_id == v.id).first()
        img = db.query(WoundImage).filter(WoundImage.visit_id == v.id).first()
        overlay_url = None
        if img:
            seg = db.query(SegmentationResult).filter(SegmentationResult.image_id == img.id).first()
            if seg:
                overlay_url = f"/api/assessments/media?path={seg.overlay_path}"

        if meas:
            points.append(HealingHistoryPoint(
                visit_id=v.id,
                visit_number=v.visit_number,
                visit_date=v.visit_date,
                area_mm2=meas.area_mm2,
                area_cm2=meas.area_cm2,
                percentage_change=meas.percentage_change,
                healing_status=meas.healing_status,
                overlay_image_url=overlay_url
            ))

    return points
