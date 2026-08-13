import os
import cv2
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, WoundImage, Calibration, SegmentationResult, Measurement
from app.ml.calibration import CalibrationEngine
from app.ml.segmentation import segmentation_engine

def generate_synthetic_wound_image(
    filename: str,
    wound_radius_x: int,
    wound_radius_y: int,
    marker_radius: int = 40
) -> str:
    """
    Generates a realistic synthetic wound photograph containing skin background,
    granulation wound region, and a clear circular calibration target (10mm).
    """
    path = os.path.join(settings.IMAGES_DIR, filename)
    if os.path.exists(path):
        return path

    w, h = 600, 500
    # Skin color background (beige/tan)
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :] = [185, 205, 235]  # BGR skin tone

    # Add subtle skin texture noise
    noise = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Draw wound tissue region in center (reddish pink granulation tissue)
    center = (280, 250)
    cv2.ellipse(img, center, (wound_radius_x, wound_radius_y), 15, 0, 360, (60, 60, 210), -1)  # Dark red
    cv2.ellipse(img, center, (int(wound_radius_x * 0.7), int(wound_radius_y * 0.7)), 15, 0, 360, (90, 90, 240), -1)  # Pink core

    # Draw Calibration Target in top right corner (White circle with dark border, diameter = marker_radius*2)
    marker_center = (480, 100)
    cv2.circle(img, marker_center, marker_radius, (255, 255, 255), -1)  # White fill
    cv2.circle(img, marker_center, marker_radius, (30, 30, 30), 3)      # Dark border
    # Text label on marker
    cv2.putText(img, "10 mm", (marker_center[0] - 25, marker_center[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    cv2.imwrite(path, img)
    return path

def seed_synthetic_demo_data(db: Session):
    """
    Seeds synthetic admin user, demo patients (PAT-1001, PAT-1002, PAT-1003),
    wound cases, and multi-visit assessments with longitudinal area reductions.
    """
    # 1. Check if admin user exists
    admin = db.query(User).filter(User.email == "admin@woundai.local").first()
    if not admin:
        admin = User(
            email="admin@woundai.local",
            hashed_password=hash_password("Admin123!"),
            full_name="Dr. Alex Rivera",
            role="Admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # 2. Check if patients exist
    if db.query(Patient).count() > 0:
        return

    # Seed Patient 1
    p1 = Patient(
        patient_code="PAT-1001",
        full_name="Demo Patient Alpha",
        age=58,
        gender="Female",
        medical_notes="Synthetic record. History of venous insufficiency and lower limb ulceration."
    )
    # Seed Patient 2
    p2 = Patient(
        patient_code="PAT-1002",
        full_name="Demo Patient Beta",
        age=64,
        gender="Male",
        medical_notes="Synthetic record. Type 2 diabetes with neuropathic foot wound."
    )
    # Seed Patient 3
    p3 = Patient(
        patient_code="PAT-1003",
        full_name="Demo Patient Gamma",
        age=71,
        gender="Male",
        medical_notes="Synthetic record. Post-surgical wound care monitoring."
    )
    db.add_all([p1, p2, p3])
    db.commit()

    # Seed Wound Case for Patient 1
    wc1 = WoundCase(
        case_code="WC-1001",
        patient_id=p1.id,
        location="Left lower leg",
        wound_type="Venous Ulcer",
        status="Active",
        notes="Venous ulcer on lateral gaiter area under compression therapy."
    )
    # Seed Wound Case for Patient 2
    wc2 = WoundCase(
        case_code="WC-1002",
        patient_id=p2.id,
        location="Right foot",
        wound_type="Diabetic Foot Ulcer",
        status="Active",
        notes="Plantnar ulcer under offloading boot protocol."
    )
    db.add_all([wc1, wc2])
    db.commit()

    # Create multi-visit trajectory for Wound Case WC-1001
    # Visit 1 (Baseline: ~320 mm²)
    # Visit 2 (1 week later: ~270 mm² -> -15.6%)
    # Visit 3 (2 weeks later: ~220 mm² -> -18.5%)
    # Visit 4 (3 weeks later: ~180 mm² -> -18.2%)

    visit_configs = [
        (1, 28, 90, 70, "Baseline initial visit. Compression applied."),
        (2, 21, 80, 62, "Visit 2. Good granulation tissue forming at margins."),
        (3, 14, 70, 53, "Visit 3. Significant epithelialization around borders."),
        (4, 7,  60, 45, "Visit 4. Wound closing cleanly. Continued healing trajectory.")
    ]

    prev_area = None

    for v_num, days_ago, rx, ry, note in visit_configs:
        v_date = datetime.utcnow() - timedelta(days=days_ago)
        visit = Visit(
            wound_id=wc1.id,
            visit_number=v_num,
            visit_date=v_date,
            clinician_id=admin.id,
            notes=note
        )
        db.add(visit)
        db.commit()

        img_filename = f"pat1001_wc1001_v{v_num}.jpg"
        img_path = generate_synthetic_wound_image(img_filename, rx, ry, marker_radius=40)

        img_bgr = cv2.imread(img_path)
        h, w = img_bgr.shape[:2]

        w_img = WoundImage(
            visit_id=visit.id,
            original_path=img_path,
            image_width=w,
            image_height=h
        )
        db.add(w_img)
        db.commit()

        # Calibration (10mm marker = 80px -> scale = 0.125 mm/px)
        marker_px = 80.0
        known_mm = 10.0
        scale = known_mm / marker_px
        cal = Calibration(
            image_id=w_img.id,
            known_size_mm=known_mm,
            marker_size_px=marker_px,
            scale_mm_per_px=scale,
            is_automatic=True
        )
        db.add(cal)
        db.commit()

        # Run Segmentation Engine to produce real mask and overlay files
        mask_path = os.path.join(settings.MASKS_DIR, f"mask_v{visit.id}.png")
        overlay_path = os.path.join(settings.OVERLAYS_DIR, f"overlay_v{visit.id}.jpg")

        seg_res = segmentation_engine.segment_wound(img_path, mask_path, overlay_path)

        seg = SegmentationResult(
            image_id=w_img.id,
            mask_path=mask_path,
            overlay_path=overlay_path,
            confidence_score=seg_res["confidence_score"],
            wound_pixel_area=seg_res["wound_pixel_area"],
            processing_status="Completed"
        )
        db.add(seg)
        db.commit()

        # Calculate exact area mm²
        area_mm2, area_cm2 = CalibrationEngine.calculate_area_mm2(seg_res["wound_pixel_area"], scale)
        width_mm = round(seg_res["width_px"] * scale, 1)
        height_mm = round(seg_res["height_px"] * scale, 1)

        pct_change = None
        healing_status = "Baseline"
        if prev_area is not None and prev_area > 0:
            pct_change = round(((prev_area - area_mm2) / prev_area) * -100, 1)
            if pct_change < -3.0:
                healing_status = "Improving"
            elif pct_change > 3.0:
                healing_status = "Increasing"
            else:
                healing_status = "Stable"

        prev_area = area_mm2

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

    db.commit()
