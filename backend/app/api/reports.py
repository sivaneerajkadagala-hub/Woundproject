import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, Measurement, WoundImage, Calibration, SegmentationResult
from app.schemas.report import ReportResponse
from app.services.report_service import PDFReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{assessment_id}", response_model=ReportResponse)
def get_report_metadata(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    visit = db.query(Visit).filter(Visit.id == assessment_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Assessment visit not found.")

    pdf_filename = f"report_visit_{visit.id}.pdf"
    pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)

    # Compile assessment data dictionary for PDF report generator
    wound = db.query(WoundCase).filter(WoundCase.id == visit.wound_id).first()
    patient = db.query(Patient).filter(Patient.id == wound.patient_id).first() if wound else None
    meas = db.query(Measurement).filter(Measurement.visit_id == visit.id).first()
    w_img = db.query(WoundImage).filter(WoundImage.visit_id == visit.id).first()
    cal = db.query(Calibration).filter(Calibration.image_id == w_img.id).first() if w_img else None
    seg = db.query(SegmentationResult).filter(SegmentationResult.image_id == w_img.id).first() if w_img else None

    data = {
        "patient_code": patient.patient_code if patient else "PAT-1001",
        "patient_name": patient.full_name if patient else "Synthetic Patient",
        "case_code": wound.case_code if wound else "WC-1001",
        "location": wound.location if wound else "Left lower leg",
        "wound_type": wound.wound_type if wound else "Venous Ulcer",
        "visit_number": visit.visit_number,
        "area_mm2": meas.area_mm2 if meas else 0.0,
        "area_cm2": meas.area_cm2 if meas else 0.0,
        "width_mm": meas.width_mm if meas else 0.0,
        "height_mm": meas.height_mm if meas else 0.0,
        "scale_mm_per_px": cal.scale_mm_per_px if cal else 0.125,
        "confidence_score": seg.confidence_score if seg else 0.92,
        "percentage_change": meas.percentage_change if meas else None,
        "healing_status": meas.healing_status if meas else "Baseline",
        "original_path": w_img.original_path if w_img else "",
        "mask_path": seg.mask_path if seg else "",
        "overlay_path": seg.overlay_path if seg else "",
        "clinician_notes": visit.notes or "Surface area assessment documented."
    }

    PDFReportGenerator.generate_assessment_pdf(data, pdf_path)

    return ReportResponse(
        assessment_id=visit.id,
        pdf_url=f"/api/reports/{visit.id}/download",
        generated_at=datetime.utcnow(),
        disclaimer="This report is an automated research prototype decision-support document and must be verified by a licensed healthcare professional."
    )

@router.get("/{assessment_id}/download")
def download_report_pdf(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    pdf_filename = f"report_visit_{assessment_id}.pdf"
    pdf_path = os.path.join(settings.REPORTS_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        # Generate on the fly
        visit = db.query(Visit).filter(Visit.id == assessment_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="Report not found")
        wound = db.query(WoundCase).filter(WoundCase.id == visit.wound_id).first()
        patient = db.query(Patient).filter(Patient.id == wound.patient_id).first() if wound else None
        meas = db.query(Measurement).filter(Measurement.visit_id == visit.id).first()
        w_img = db.query(WoundImage).filter(WoundImage.visit_id == visit.id).first()
        cal = db.query(Calibration).filter(Calibration.image_id == w_img.id).first() if w_img else None
        seg = db.query(SegmentationResult).filter(SegmentationResult.image_id == w_img.id).first() if w_img else None

        data = {
            "patient_code": patient.patient_code if patient else "PAT-1001",
            "patient_name": patient.full_name if patient else "Synthetic Patient",
            "case_code": wound.case_code if wound else "WC-1001",
            "location": wound.location if wound else "Left lower leg",
            "wound_type": wound.wound_type if wound else "Venous Ulcer",
            "visit_number": visit.visit_number,
            "area_mm2": meas.area_mm2 if meas else 0.0,
            "area_cm2": meas.area_cm2 if meas else 0.0,
            "width_mm": meas.width_mm if meas else 0.0,
            "height_mm": meas.height_mm if meas else 0.0,
            "scale_mm_per_px": cal.scale_mm_per_px if cal else 0.125,
            "confidence_score": seg.confidence_score if seg else 0.92,
            "percentage_change": meas.percentage_change if meas else None,
            "healing_status": meas.healing_status if meas else "Baseline",
            "original_path": w_img.original_path if w_img else "",
            "mask_path": seg.mask_path if seg else "",
            "overlay_path": seg.overlay_path if seg else "",
            "clinician_notes": visit.notes or "Surface area assessment documented."
        }
        PDFReportGenerator.generate_assessment_pdf(data, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"Wound_Report_Visit_{assessment_id}.pdf")
