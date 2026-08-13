from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    wound_id = Column(Integer, ForeignKey("wound_cases.id", ondelete="CASCADE"), nullable=False)
    visit_number = Column(Integer, nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow)
    clinician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    wound_case = relationship("WoundCase", back_populates="visits")
    clinician = relationship("User", back_populates="visits")
    image = relationship("WoundImage", uselist=False, back_populates="visit", cascade="all, delete-orphan")
    measurement = relationship("Measurement", uselist=False, back_populates="visit", cascade="all, delete-orphan")


class WoundImage(Base):
    __tablename__ = "wound_images"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, unique=True)
    original_path = Column(String, nullable=False)
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    visit = relationship("Visit", back_populates="image")
    calibration = relationship("Calibration", uselist=False, back_populates="image", cascade="all, delete-orphan")
    segmentation = relationship("SegmentationResult", uselist=False, back_populates="image", cascade="all, delete-orphan")


class Calibration(Base):
    __tablename__ = "calibrations"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("wound_images.id", ondelete="CASCADE"), nullable=False, unique=True)
    known_size_mm = Column(Float, nullable=False)
    marker_size_px = Column(Float, nullable=False)
    scale_mm_per_px = Column(Float, nullable=False) # known_size_mm / marker_size_px
    is_automatic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("WoundImage", back_populates="calibration")


class SegmentationResult(Base):
    __tablename__ = "segmentation_results"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("wound_images.id", ondelete="CASCADE"), nullable=False, unique=True)
    mask_path = Column(String, nullable=False)
    overlay_path = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False) # e.g. 0.94 (94%)
    wound_pixel_area = Column(Integer, nullable=False)
    processing_status = Column(String, default="Completed") # Completed, Failed, Manual_Adjusted
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("WoundImage", back_populates="segmentation")


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, unique=True)
    area_mm2 = Column(Float, nullable=False)
    area_cm2 = Column(Float, nullable=False)
    width_mm = Column(Float, nullable=False)
    height_mm = Column(Float, nullable=False)
    percentage_change = Column(Float, nullable=True) # Percentage change from previous visit
    healing_status = Column(String, default="Baseline") # Baseline, Improving, Stable, Increasing
    created_at = Column(DateTime, default=datetime.utcnow)

    visit = relationship("Visit", back_populates="measurement")
