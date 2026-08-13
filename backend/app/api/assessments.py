import os
import uuid
import cv2
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, WoundImage, Calibration, SegmentationResult, Measurement
from app.schemas.assessment import (
    ImageUploadResponse, CalibrationRequest, CalibrationResponse,
    SegmentationRequest, SegmentationResponse, AreaCalculationRequest,
    MeasurementResponse, AssessmentDetailResponse
)
from app.ml.calibration import CalibrationEngine
from app.ml.segmentation import segmentation_engine

router = APIRouter(prefix="/assessments", tags=["Wound Assessments"])

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_wound_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG, JPEG, or PNG image.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Unsupported image extension. Allowed: .jpg, .jpeg, .png")

    filename = f"upload_{uuid.uuid4().hex[:10]}{ext}"
    filepath = os.path.join(settings.IMAGES_DIR, filename)

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 20MB.")

    with open(filepath, "wb") as f:
        f.write(contents)

    img = cv2.imread(filepath)
    if img is None:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail="Corrupted image file. Unable to decode.")

    h, w = img.shape[:2]

    # Create temporary WoundImage database record
    # visit_id will be linked when area calculation is finalized
    # For transient upload, create a standalone image record
    # Note: image_id will be referenced in calibration and segmentation steps
    return ImageUploadResponse(
        image_id=0, # Client will use temporary filepath or database ID
        original_path=filepath,
        image_width=w,
        image_height=h,
        message="Wound image uploaded successfully."
    )

@router.post("/calibrate", response_model=CalibrationResponse)
def calibrate_image(
    req: CalibrationRequest,
    image_path: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server.")

    if req.marker_size_px and req.marker_size_px > 0:
        res = CalibrationEngine.calculate_scale_manual(req.known_size_mm, req.marker_size_px)
    else:
        res = CalibrationEngine.detect_marker_cv(image_path, req.known_size_mm)

    return CalibrationResponse(
        id=0,
        image_id=req.image_id,
        known_size_mm=res["known_size_mm"],
        marker_size_px=res["marker_size_px"],
        scale_mm_per_px=res["scale_mm_per_px"],
        is_automatic=res.get("is_automatic", False)
    )

@router.post("/segment", response_model=SegmentationResponse)
def segment_image(
    req: SegmentationRequest,
    image_path: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server.")

    mask_filename = f"mask_{uuid.uuid4().hex[:10]}.png"
    overlay_filename = f"overlay_{uuid.uuid4().hex[:10]}.jpg"

    mask_path = os.path.join(settings.MASKS_DIR, mask_filename)
    overlay_path = os.path.join(settings.OVERLAYS_DIR, overlay_filename)

    res = segmentation_engine.segment_wound(
        image_path=image_path,
        output_mask_path=mask_path,
        output_overlay_path=overlay_path,
        threshold=req.threshold
    )

    return SegmentationResponse(
        id=0,
        image_id=req.image_id,
        mask_path=mask_path,
        overlay_path=overlay_path,
        confidence_score=res["confidence_score"],
        wound_pixel_area=res["wound_pixel_area"],
        processing_status=res["processing_status"]
    )

@router.post("/calculate-area", response_model=AssessmentDetailResponse)
def calculate_area_and_save(
    req: AreaCalculationRequest,
    image_path: str = Form(...),
    mask_path: str = Form(...),
    overlay_path: str = Form(...),
    confidence_score: float = Form(0.92),
    wound_pixel_area: int = Form(...),
    scale_mm_per_px: float = Form(...),
    marker_size_px: float = Form(...),
    is_automatic_calibration: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wound = db.query(WoundCase).filter(WoundCase.id == req.wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound case not found.")

    # Determine visit number
    visit_count = db.query(Visit).filter(Visit.wound_id == req.wound_id).count()
    v_num = visit_count + 1

    # Create Visit
    visit = Visit(
        wound_id=req.wound_id,
        visit_number=v_num,
        visit_date=datetime.utcnow(),
        clinician_id=current_user.id,
        notes=req.notes
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    # Read image dimensions
    img = cv2.imread(image_path)
    h, w = (img.shape[0], img.shape[1]) if img is not None else (500, 600)

    # Create WoundImage
    w_img = WoundImage(
        visit_id=visit.id,
        original_path=image_path,
        image_width=w,
        image_height=h
    )
    db.add(w_img)
    db.commit()
    db.refresh(w_img)

    # Save Calibration
    cal = Calibration(
        image_id=w_img.id,
        known_size_mm=req.known_size_mm,
        marker_size_px=marker_size_px,
        scale_mm_per_px=scale_mm_per_px,
        is_automatic=is_automatic_calibration
    )
    db.add(cal)

    # Save SegmentationResult
    seg = SegmentationResult(
        image_id=w_img.id,
        mask_path=mask_path,
        overlay_path=overlay_path,
        confidence_score=confidence_score,
        wound_pixel_area=wound_pixel_area,
        processing_status="Completed"
    )
    db.add(seg)

    # Calculate mm² and cm²
    area_mm2, area_cm2 = CalibrationEngine.calculate_area_mm2(wound_pixel_area, scale_mm_per_px)
    width_mm = round(np.sqrt(wound_pixel_area) * scale_mm_per_px, 1)
    height_mm = round(np.sqrt(wound_pixel_area) * scale_mm_per_px, 1)

    # Calculate percentage change vs previous visit
    prev_visit = db.query(Visit).filter(
        Visit.wound_id == req.wound_id,
        Visit.id != visit.id
    ).order_by(Visit.visit_number.desc()).first()

    pct_change = None
    healing_status = "Baseline"

    if prev_visit:
        prev_meas = db.query(Measurement).filter(Measurement.visit_id == prev_visit.id).first()
        if prev_meas and prev_meas.area_mm2 > 0:
            pct_change = round(((prev_meas.area_mm2 - area_mm2) / prev_meas.area_mm2) * -100, 1)
            if pct_change < -3.0:
                healing_status = "Improving"
            elif pct_change > 3.0:
                healing_status = "Increasing"
            else:
                healing_status = "Stable"

    meas = Measurement(
        visit_id=visit.id,
        area_mm2=area_mm2,
        area_cm2=area_cm2,
        width_mm=width_mm,
        height_mm=height_mm,
        percentage_change=pct_change,
        healing_status=healing_status
    )
    db.add(meas)
    db.commit()

    return AssessmentDetailResponse(
        visit_id=visit.id,
        wound_id=req.wound_id,
        visit_number=visit.visit_number,
        visit_date=visit.visit_date,
        clinician_notes=visit.notes,
        original_image_url=f"/api/assessments/media?path={image_path}",
        mask_image_url=f"/api/assessments/media?path={mask_path}",
        overlay_image_url=f"/api/assessments/media?path={overlay_path}",
        image_width=w,
        image_height=h,
        known_size_mm=req.known_size_mm,
        marker_size_px=marker_size_px,
        scale_mm_per_px=scale_mm_per_px,
        is_automatic_calibration=is_automatic_calibration,
        confidence_score=confidence_score,
        wound_pixel_area=wound_pixel_area,
        area_mm2=area_mm2,
        area_cm2=area_cm2,
        width_mm=width_mm,
        height_mm=height_mm,
        percentage_change=pct_change,
        healing_status=healing_status
    )

@router.get("/{id}", response_model=AssessmentDetailResponse)
def get_assessment_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    visit = db.query(Visit).filter(Visit.id == id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Assessment visit record not found.")

    meas = db.query(Measurement).filter(Measurement.visit_id == visit.id).first()
    w_img = db.query(WoundImage).filter(WoundImage.visit_id == visit.id).first()

    if not meas or not w_img:
        raise HTTPException(status_code=404, detail="Incomplete assessment measurement data.")

    cal = db.query(Calibration).filter(Calibration.image_id == w_img.id).first()
    seg = db.query(SegmentationResult).filter(SegmentationResult.image_id == w_img.id).first()

    return AssessmentDetailResponse(
        visit_id=visit.id,
        wound_id=visit.wound_id,
        visit_number=visit.visit_number,
        visit_date=visit.visit_date,
        clinician_notes=visit.notes,
        original_image_url=f"/api/assessments/media?path={w_img.original_path}",
        mask_image_url=f"/api/assessments/media?path={seg.mask_path if seg else ''}",
        overlay_image_url=f"/api/assessments/media?path={seg.overlay_path if seg else ''}",
        image_width=w_img.image_width,
        image_height=w_img.image_height,
        known_size_mm=cal.known_size_mm if cal else 10.0,
        marker_size_px=cal.marker_size_px if cal else 80.0,
        scale_mm_per_px=cal.scale_mm_per_px if cal else 0.125,
        is_automatic_calibration=cal.is_automatic if cal else True,
        confidence_score=seg.confidence_score if seg else 0.9,
        wound_pixel_area=seg.wound_pixel_area if seg else 0,
        area_mm2=meas.area_mm2,
        area_cm2=meas.area_cm2,
        width_mm=meas.width_mm,
        height_mm=meas.height_mm,
        percentage_change=meas.percentage_change,
        healing_status=meas.healing_status
    )

@router.get("/media")
def serve_media_file(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(path)
