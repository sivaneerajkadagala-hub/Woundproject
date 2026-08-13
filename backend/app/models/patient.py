from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, unique=True, index=True, nullable=False) # e.g. PAT-1001
    full_name = Column(String, nullable=False) # Synthetic demo name
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    medical_notes = Column(String, nullable=True)
    is_archived = Column(String, default="Active") # Active, Archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wound_cases = relationship("WoundCase", back_populates="patient", cascade="all, delete-orphan")
