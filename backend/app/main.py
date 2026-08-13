import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.services.seed_service import seed_synthetic_demo_data
from app.models.patient import Patient
from app.models.wound import WoundCase
from app.models.assessment import Visit, Measurement
from app.api import auth, patients, wounds, assessments, reports, assistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wound_ai.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed demo data if database is fresh
    db = next(get_db())
    try:
        logger.info("Checking synthetic demo dataset...")
        seed_synthetic_demo_data(db)
        logger.info("Synthetic demo dataset ready.")
    except Exception as e:
        logger.error(f"Error seeding demo dataset: {e}")
    finally:
        db.close()
        
    yield
    logger.info("Shutting down Wound AI Platform server...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Grade AI Wound Segmentation & Healing Monitoring System (U-Net decision support prototype)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media storage directory
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(wounds.router, prefix=settings.API_V1_STR)
app.include_router(assessments.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "model_status": "Pretrained U-Net Ready"
    }

@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_patients = db.query(Patient).count()
    active_wounds = db.query(WoundCase).filter(WoundCase.status == "Active").count()
    
    total_measurements = db.query(Measurement).count()
    improving_wounds = db.query(Measurement).filter(Measurement.healing_status == "Improving").count()
    attention_wounds = db.query(WoundCase).filter(WoundCase.status == "Attention Required").count()

    # Recent assessments list
    recent_visits = db.query(Visit).order_by(Visit.created_at.desc()).limit(5).all()
    recent_assessments = []
    for v in recent_visits:
        w = db.query(WoundCase).filter(WoundCase.id == v.wound_id).first()
        p = db.query(Patient).filter(Patient.id == w.patient_id).first() if w else None
        m = db.query(Measurement).filter(Measurement.visit_id == v.id).first()
        if w and p and m:
            recent_assessments.append({
                "visit_id": v.id,
                "patient_code": p.patient_code,
                "patient_name": p.full_name,
                "case_code": w.case_code,
                "location": w.location,
                "visit_date": v.visit_date.isoformat(),
                "area_mm2": m.area_mm2,
                "percentage_change": m.percentage_change,
                "healing_status": m.healing_status
            })

    return {
        "total_patients": total_patients,
        "active_wounds": active_wounds,
        "total_measurements": total_measurements,
        "improving_wounds": improving_wounds,
        "attention_wounds": attention_wounds,
        "recent_assessments": recent_assessments
    }
