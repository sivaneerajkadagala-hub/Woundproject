from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ImageUploadResponse(BaseModel):
    image_id: int
    original_path: str
    image_width: int
    image_height: int
    message: str

class CalibrationRequest(BaseModel):
    image_id: int
    known_size_mm: float = 10.0
    marker_size_px: Optional[float] = None
    manual_endpoint: Optional[dict] = None # {"x1": int, "y1": int, "x2": int, "y2": int}

class CalibrationResponse(BaseModel):
    id: int
    image_id: int
    known_size_mm: float
    marker_size_px: float
    scale_mm_per_px: float
    is_automatic: bool

class SegmentationRequest(BaseModel):
    image_id: int
    threshold: float = 0.5
    known_size_mm: float = 10.0
    marker_size_px: Optional[float] = None

class SegmentationResponse(BaseModel):
    id: int
    image_id: int
    mask_path: str
    overlay_path: str
    confidence_score: float
    wound_pixel_area: int
    processing_status: str

class AreaCalculationRequest(BaseModel):
    image_id: int
    visit_id: Optional[int] = None
    wound_id: int
    known_size_mm: float = 10.0
    marker_size_px: Optional[float] = None
    notes: Optional[str] = None

class MeasurementResponse(BaseModel):
    id: int
    visit_id: int
    area_mm2: float
    area_cm2: float
    width_mm: float
    height_mm: float
    percentage_change: Optional[float] = None
    healing_status: str
    created_at: datetime

class AssessmentDetailResponse(BaseModel):
    visit_id: int
    wound_id: int
    visit_number: int
    visit_date: datetime
    clinician_notes: Optional[str] = None
    original_image_url: str
    mask_image_url: str
    overlay_image_url: str
    image_width: int
    image_height: int
    known_size_mm: float
    marker_size_px: float
    scale_mm_per_px: float
    is_automatic_calibration: bool
    confidence_score: float
    wound_pixel_area: int
    area_mm2: float
    area_cm2: float
    width_mm: float
    height_mm: float
    percentage_change: Optional[float] = None
    healing_status: str

class HealingHistoryPoint(BaseModel):
    visit_id: int
    visit_number: int
    visit_date: datetime
    area_mm2: float
    area_cm2: float
    percentage_change: Optional[float] = None
    healing_status: str
    overlay_image_url: Optional[str] = None
