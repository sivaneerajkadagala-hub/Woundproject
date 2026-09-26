"""
End-to-end integration tests for the wound assessment workflow.

Tests cover:
1. Successful image upload (WoundImage record created, image_id returned, relative URL)
2. Calibration (pixel-to-mm calculation, squared scale for area)
3. Segmentation (mask generated, wound pixels detected, method reported)
4. Width/height from bounding box (not sqrt(pixel_area))
5. Save assessment (complete persistence)
6. Path traversal rejection
7. Authentication enforcement on protected endpoints
8. Report authorization (unauthenticated download rejected)
"""
import os
import io
import pytest
import cv2
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, WoundImage, Calibration, SegmentationResult, Measurement
from app.main import app
from app.core.config import settings


# --- Test Database Setup ---

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def auth_client(test_db):
    """Create a TestClient with a pre-seeded user and return (client, token)."""
    # Create test user
    user = User(
        email="test@woundai.com",
        hashed_password=hash_password("Test123!"),
        full_name="Test Clinician",
        role="Clinician",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()

    # Create test patient and wound
    patient = Patient(
        patient_code="PAT-TEST1",
        full_name="Test Patient",
        age=50,
        gender="Male",
        medical_notes="Test record"
    )
    test_db.add(patient)
    test_db.commit()

    wound = WoundCase(
        case_code="WC-TEST1",
        patient_id=patient.id,
        location="Left lower leg",
        wound_type="Venous Ulcer",
        status="Active",
        notes="Test wound"
    )
    test_db.add(wound)
    test_db.commit()

    client = TestClient(app)

    # Login
    response = client.post("/api/auth/login", json={
        "email": "test@woundai.com",
        "password": "Test123!"
    })
    token = response.json()["access_token"]
    return client, token, wound.id


def create_test_image_bytes(width=600, height=500):
    """Create a synthetic wound image as bytes for upload testing."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = [185, 205, 235]  # Skin tone BGR
    # Draw wound region (red/pink)
    cv2.ellipse(img, (280, 250), (60, 45), 15, 0, 360, (60, 60, 210), -1)
    cv2.ellipse(img, (280, 250), (42, 32), 15, 0, 360, (90, 90, 240), -1)
    # Draw calibration marker
    cv2.circle(img, (480, 100), 40, (255, 255, 255), -1)
    cv2.circle(img, (480, 100), 40, (30, 30, 30), 3)

    # Encode to JPEG
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()


# --- Test 1: Successful Upload ---

class TestUpload:
    def test_successful_upload_creates_woundimage(self, auth_client):
        """Verify upload creates a WoundImage DB record and returns image_id + relative URL."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        img_bytes = create_test_image_bytes()
        response = client.post(
            "/api/assessments/upload",
            headers=headers,
            files={"file": ("test_wound.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["image_id"] > 0, "image_id should be a real DB ID, not 0"
        assert data["image_width"] > 0
        assert data["image_height"] > 0
        assert "image_url" in data
        assert data["image_url"].startswith("/api/assessments/media")
        # Path should be relative, not absolute
        assert ":" not in data["original_path"], "Path should be relative, not absolute"
        assert not data["original_path"].startswith("/"), "Path should be relative to STORAGE_DIR"

    def test_upload_rejects_non_image(self, auth_client):
        """Verify non-image files are rejected."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/assessments/upload",
            headers=headers,
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
        assert response.status_code == 400

    def test_upload_requires_auth(self, test_db):
        """Verify upload endpoint requires authentication."""
        client = TestClient(app)
        img_bytes = create_test_image_bytes()
        response = client.post(
            "/api/assessments/upload",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        assert response.status_code == 401


# --- Test 2: Calibration ---

class TestCalibration:
    def test_calibration_scale_calculation(self, auth_client):
        """Verify pixel-to-mm calculation and squared scale for area."""
        from app.ml.calibration import CalibrationEngine

        # 100px = 10mm -> scale = 0.1 mm/px
        res = CalibrationEngine.calculate_scale_manual(known_size_mm=10.0, marker_size_px=100.0)
        assert res["scale_mm_per_px"] == 0.1

        # Area: 20000 px * (0.1)^2 = 200 mm²
        area_mm2, area_cm2 = CalibrationEngine.calculate_area_mm2(20000, 0.1)
        assert area_mm2 == 200.0
        assert area_cm2 == 2.0

    def test_calibration_via_api(self, auth_client):
        """Verify calibration endpoint works with uploaded image."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        # Upload first
        img_bytes = create_test_image_bytes()
        upload_res = client.post(
            "/api/assessments/upload",
            headers=headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        image_path = upload_res.json()["original_path"]
        image_id = upload_res.json()["image_id"]

        # Calibrate
        cal_res = client.post(
            "/api/assessments/calibrate",
            headers=headers,
            data={"image_id": image_id, "known_size_mm": "10.0", "image_path": image_path}
        )
        assert cal_res.status_code == 200
        data = cal_res.json()
        assert data["scale_mm_per_px"] > 0
        assert data["known_size_mm"] == 10.0


# --- Test 3: Segmentation ---

class TestSegmentation:
    def test_segmentation_generates_mask(self, auth_client):
        """Verify mask is generated, wound pixels detected, and method reported."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        # Upload
        img_bytes = create_test_image_bytes()
        upload_res = client.post(
            "/api/assessments/upload",
            headers=headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        image_path = upload_res.json()["original_path"]
        image_id = upload_res.json()["image_id"]

        # Segment
        seg_res = client.post(
            "/api/assessments/segment",
            headers=headers,
            data={"image_id": image_id, "image_path": image_path, "threshold": "0.5"}
        )
        assert seg_res.status_code == 200
        data = seg_res.json()
        assert data["wound_pixel_area"] > 0, "Should detect wound pixels"
        assert data["width_px"] > 0, "Should report bounding box width"
        assert data["height_px"] > 0, "Should report bounding box height"
        assert data["segmentation_method"] in ["cv_color", "unet"]
        assert data["processing_status"] == "Completed"
        # Paths should be relative
        assert ":" not in data["mask_path"]
        assert ":" not in data["overlay_path"]


# --- Test 4: Width/Height from Bounding Box ---

class TestWidthHeight:
    def test_width_height_from_bounding_box(self):
        """Verify width/height come from the mask bounding box, not sqrt(area)."""
        from app.ml.segmentation import segmentation_engine
        import tempfile

        # Create a clearly non-square wound image (wide wound)
        img = np.zeros((500, 600, 3), dtype=np.uint8)
        img[:, :] = [185, 205, 235]
        # Draw a wide wound (100px wide, 30px tall)
        cv2.ellipse(img, (300, 250), (80, 20), 0, 0, 360, (60, 60, 210), -1)
        cv2.circle(img, (480, 100), 40, (255, 255, 255), -1)
        cv2.circle(img, (480, 100), 40, (30, 30, 30), 3)

        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "test.jpg")
            mask_path = os.path.join(tmpdir, "mask.png")
            overlay_path = os.path.join(tmpdir, "overlay.jpg")
            cv2.imwrite(img_path, img)

            res = segmentation_engine.segment_wound(img_path, mask_path, overlay_path)

            # Width should be significantly larger than height for this wide wound
            assert res["width_px"] > res["height_px"], \
                f"Width ({res['width_px']}) should be > height ({res['height_px']}) for wide wound"
            # Verify it's NOT sqrt(area) which would give equal width/height
            sqrt_area = int(np.sqrt(res["wound_pixel_area"]))
            assert res["width_px"] != sqrt_area or res["height_px"] != sqrt_area, \
                "Width/height should not both equal sqrt(area)"


# --- Test 5: Save Assessment ---

class TestSaveAssessment:
    def test_complete_assessment_workflow(self, auth_client):
        """Verify the complete assessment can be persisted."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        # Upload
        img_bytes = create_test_image_bytes()
        upload_res = client.post(
            "/api/assessments/upload",
            headers=headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        image_id = upload_res.json()["image_id"]
        image_path = upload_res.json()["original_path"]

        # Calibrate
        cal_res = client.post(
            "/api/assessments/calibrate",
            headers=headers,
            data={"image_id": image_id, "known_size_mm": "10.0", "image_path": image_path}
        )
        scale = cal_res.json()["scale_mm_per_px"]
        marker_px = cal_res.json()["marker_size_px"]

        # Segment
        seg_res = client.post(
            "/api/assessments/segment",
            headers=headers,
            data={"image_id": image_id, "image_path": image_path, "threshold": "0.5"}
        )
        mask_path = seg_res.json()["mask_path"]
        overlay_path = seg_res.json()["overlay_path"]
        wound_px_area = seg_res.json()["wound_pixel_area"]
        w_px = seg_res.json()["width_px"]
        h_px = seg_res.json()["height_px"]
        conf = seg_res.json()["confidence_score"]
        method = seg_res.json()["segmentation_method"]

        # Save assessment
        save_res = client.post(
            "/api/assessments/calculate-area",
            headers=headers,
            data={
                "image_id": image_id,
                "wound_id": wound_id,
                "image_path": image_path,
                "mask_path": mask_path,
                "overlay_path": overlay_path,
                "confidence_score": str(conf),
                "wound_pixel_area": str(wound_px_area),
                "width_px": str(w_px),
                "height_px": str(h_px),
                "segmentation_method": method,
                "scale_mm_per_px": str(scale),
                "marker_size_px": str(marker_px),
                "known_size_mm": "10.0",
                "is_automatic_calibration": "true",
                "notes": "Integration test assessment"
            }
        )
        assert save_res.status_code == 200
        data = save_res.json()
        assert data["visit_id"] > 0
        assert data["visit_number"] == 1
        assert data["area_mm2"] > 0
        assert data["area_cm2"] > 0
        assert data["width_mm"] > 0
        assert data["height_mm"] > 0
        assert data["segmentation_method"] in ["cv_color", "unet"]
        assert data["healing_status"] == "Baseline"

        # Retrieve assessment
        get_res = client.get(f"/api/assessments/{data['visit_id']}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["area_mm2"] == data["area_mm2"]


# --- Test 6: Path Traversal ---

class TestPathTraversal:
    def test_path_traversal_rejected(self, auth_client):
        """Verify malicious paths are rejected."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        # Try path traversal
        response = client.get(
            "/api/assessments/media",
            headers=headers,
            params={"path": "../../../etc/passwd"}
        )
        assert response.status_code in [403, 404]

    def test_path_traversal_absolute_rejected(self, auth_client):
        """Verify absolute paths outside storage are rejected."""
        client, token, wound_id = auth_client
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/assessments/media",
            headers=headers,
            params={"path": "/etc/passwd"}
        )
        assert response.status_code in [403, 404]

    def test_media_requires_auth(self, test_db):
        """Verify media endpoint requires authentication."""
        client = TestClient(app)
        response = client.get("/api/assessments/media", params={"path": "images/test.jpg"})
        assert response.status_code == 401


# --- Test 7: Authentication ---

class TestAuthentication:
    def test_protected_endpoints_require_auth(self, test_db):
        """Verify protected endpoints reject unauthenticated requests."""
        client = TestClient(app)

        endpoints = [
            ("GET", "/api/patients"),
            ("GET", "/api/wounds"),
            ("GET", "/api/auth/me"),
            ("GET", "/api/dashboard/summary"),
            ("GET", "/api/dashboard/healing-trend"),
        ]
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            assert response.status_code == 401, f"{method} {path} should require auth"

    def test_invalid_token_rejected(self, test_db):
        """Verify invalid tokens are rejected."""
        client = TestClient(app)
        response = client.get("/api/patients", headers={"Authorization": "Bearer invalidtoken123"})
        assert response.status_code == 401


# --- Test 8: Report Authorization ---

class TestReportAuth:
    def test_report_download_requires_auth(self, test_db):
        """Verify an unauthenticated user cannot download reports."""
        client = TestClient(app)
        response = client.get("/api/reports/1/download")
        assert response.status_code == 401

    def test_report_metadata_requires_auth(self, test_db):
        """Verify report metadata endpoint requires auth."""
        client = TestClient(app)
        response = client.get("/api/reports/1")
        assert response.status_code == 401


# --- Test 9: Role-Based Access Control ---

class TestRBAC:
    def _create_user_and_get_token(self, db, email, role):
        """Helper to create a user with a specific role and get a token."""
        from app.core.security import hash_password, create_access_token
        user = User(
            email=email,
            hashed_password=hash_password("Test123!"),
            full_name=f"Test {role}",
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=user.id, role=user.role)
        return token, user.id

    def test_staff_cannot_delete_patient(self, test_db):
        """Staff role should not be able to delete patients (Admin only)."""
        token, _ = self._create_user_and_get_token(test_db, "staff@woundai.com", "Staff")
        patient = Patient(
            patient_code="PAT-RBAC1",
            full_name="RBAC Test Patient",
            age=50,
            gender="Male",
            medical_notes="Test"
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        client = TestClient(app)
        response = client.delete(
            f"/api/patients/{patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_clinician_cannot_delete_patient(self, test_db):
        """Clinician role should not be able to delete patients (Admin only)."""
        token, _ = self._create_user_and_get_token(test_db, "clinician@woundai.com", "Clinician")
        patient = Patient(
            patient_code="PAT-RBAC2",
            full_name="RBAC Test Patient 2",
            age=50,
            gender="Male",
            medical_notes="Test"
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        client = TestClient(app)
        response = client.delete(
            f"/api/patients/{patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_admin_can_delete_patient(self, test_db):
        """Admin role should be able to delete patients."""
        token, _ = self._create_user_and_get_token(test_db, "admin2@woundai.com", "Admin")
        patient = Patient(
            patient_code="PAT-RBAC3",
            full_name="RBAC Test Patient 3",
            age=50,
            gender="Male",
            medical_notes="Test"
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        client = TestClient(app)
        response = client.delete(
            f"/api/patients/{patient.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204

    def test_staff_cannot_archive_wound(self, test_db):
        """Staff role should not be able to archive wound cases (Admin only)."""
        token, _ = self._create_user_and_get_token(test_db, "staff2@woundai.com", "Staff")
        patient = Patient(
            patient_code="PAT-RBAC4",
            full_name="RBAC Test Patient 4",
            age=50,
            gender="Male",
            medical_notes="Test"
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        wound = WoundCase(
            case_code="WC-RBAC1",
            patient_id=patient.id,
            location="Left leg",
            wound_type="Venous Ulcer",
            status="Active",
            notes="Test"
        )
        test_db.add(wound)
        test_db.commit()
        test_db.refresh(wound)

        client = TestClient(app)
        response = client.delete(
            f"/api/wounds/{wound.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_clinician_can_create_patient(self, test_db):
        """Clinician role should be able to create patients."""
        token, _ = self._create_user_and_get_token(test_db, "clinician2@woundai.com", "Clinician")
        client = TestClient(app)
        response = client.post(
            "/api/patients",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "New Patient", "age": 45, "gender": "Female", "medical_notes": "Test"}
        )
        assert response.status_code == 201

    def test_audit_logs_admin_only(self, test_db):
        """Audit logs endpoint should be Admin only."""
        staff_token, _ = self._create_user_and_get_token(test_db, "staff3@woundai.com", "Staff")
        admin_token, _ = self._create_user_and_get_token(test_db, "admin3@woundai.com", "Admin")
        client = TestClient(app)

        # Staff should be forbidden
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code == 403

        # Admin should have access
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


# --- Test 10: Audit Logging ---

class TestAuditLog:
    def test_login_creates_audit_log(self, test_db):
        """Verify that a login attempt creates an audit log entry."""
        from app.core.security import hash_password
        from app.models.audit import AuditLog

        user = User(
            email="audit-test@woundai.com",
            hashed_password=hash_password("Test123!"),
            full_name="Audit Test User",
            role="Admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        client = TestClient(app)
        response = client.post("/api/auth/login", json={
            "email": "audit-test@woundai.com",
            "password": "Test123!"
        })
        assert response.status_code == 200

        # Check audit log was created
        logs = test_db.query(AuditLog).filter(AuditLog.action == "login").all()
        assert len(logs) >= 1
        assert logs[-1].user_id == user.id

    def test_patient_create_creates_audit_log(self, test_db):
        """Verify that creating a patient creates an audit log entry."""
        from app.core.security import hash_password, create_access_token
        from app.models.audit import AuditLog

        user = User(
            email="audit-admin@woundai.com",
            hashed_password=hash_password("Test123!"),
            full_name="Audit Admin",
            role="Admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        token = create_access_token(subject=user.id, role=user.role)
        client = TestClient(app)
        response = client.post(
            "/api/patients",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Audit Patient", "age": 50, "gender": "Male", "medical_notes": "Test"}
        )
        assert response.status_code == 201

        logs = test_db.query(AuditLog).filter(AuditLog.action == "patient_create").all()
        assert len(logs) >= 1
        assert logs[-1].user_id == user.id
