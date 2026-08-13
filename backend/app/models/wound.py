from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class WoundCase(Base):
    __tablename__ = "wound_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_code = Column(String, unique=True, index=True, nullable=False) # e.g. WC-1001
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    location = Column(String, nullable=False) # Left lower leg, Right foot, Forearm, Heel
    wound_type = Column(String, nullable=False) # Venous Ulcer, Diabetic Foot Ulcer, Pressure Injury, Surgical
    status = Column(String, default="Active") # Active, Healing, Closed, Attention Required
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="wound_cases")
    visits = relationship("Visit", back_populates="wound_case", cascade="all, delete-orphan", order_by="Visit.visit_number")
