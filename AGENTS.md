# Wound AI Platform - Project Guide

## Overview
AI Wound Segmentation & Healing Monitoring System. Backend in FastAPI (Python), frontend in React/TypeScript with Vite.

## Project Structure
- `backend/` - FastAPI backend (Python 3.13)
  - `app/api/` - API route handlers (auth, patients, wounds, assessments, reports)
  - `app/core/` - Config, database, security
  - `app/models/` - SQLAlchemy models
  - `app/schemas/` - Pydantic schemas
  - `app/services/` - Business logic (seed, report, audit)
  - `app/ml/` - ML pipeline (segmentation, calibration)
  - `alembic/` - Database migrations
  - `tests/` - Pytest tests (29 tests)
  - `venv/` - Python virtual environment (Windows)
- `frontend/` - React + TypeScript + Vite
  - `src/pages/` - Page components
  - `src/components/` - Reusable components
  - `src/test/` - Vitest test setup and tests (13 tests)

## Commands

### Backend
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v          # Run all backend tests
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000  # Start dev server
.\venv\Scripts\python.exe -m alembic upgrade head      # Apply migrations
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "desc"  # Create migration
```

### Frontend
```powershell
# Node.js portable at C:\Users\bayal\node_portable
$env:Path = "C:\Users\bayal\node_portable;$env:Path"
cd frontend
npm run build       # Build for production (tsc && vite build)
npm run test        # Run vitest tests (single run)
npm run test:watch  # Run vitest in watch mode
npm run dev         # Start dev server
```

## Configuration

### Environment Variables
- **SECRET_KEY** (required) - JWT signing key. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. No hardcoded fallback in production. Dev-only fallback active under pytest or `DEV_ALLOW_INSECURE_SECRET=1`.
- **CORS_ORIGINS_STR** - Comma-separated allowed origins. No wildcard (`*`) allowed.
- **DATABASE_URL** - SQLite for dev (`sqlite:///./wound_app.db`), Postgres for Docker.
- **UNET_CHECKPOINT_PATH** - Optional U-Net model checkpoint. CV color segmentation is the default fallback.
- **AIMESH_BASE_URL / AIMESH_API_KEY** - Optional external AI service.

### Local Dev Setup
1. `backend/.env` file exists (gitignored) with dev values. Copy from `.env.example` if missing.
2. Database auto-creates on first run via SQLAlchemy `create_all`.

## Security Features
- **JWT auth** - Bearer token, 7-day expiry, HS256 algorithm
- **RBAC** - Three roles: Admin, Clinician, Staff
  - Admin: full access (delete patients, archive wounds, view audit logs)
  - Clinician: create/update patients and wounds, assessments, reports
  - Staff: read-only access
- **CORS** - Explicit origins only, no wildcards
- **Path traversal protection** - Media endpoint validates paths stay within storage dir
- **Audit logging** - All write operations and logins logged via `app.services.audit_service.log_action`
- **Password hashing** - bcrypt via passlib

## Segmentation Pipeline
- Default: CV color-based HSV segmentation (reliable, no model required)
- Optional: U-Net inference when `UNET_CHECKPOINT_PATH` points to a valid checkpoint
- HSV detection uses S>=100 threshold to separate wound tissue (high saturation) from skin (low saturation)
- Synthetic wound images use olive-tan skin tone (H~25) to avoid false positives from reddish skin tones

## Key Files
- `backend/app/core/config.py` - Settings with env validation
- `backend/app/api/auth.py` - Auth routes + `require_role` dependency
- `backend/app/services/audit_service.py` - Audit logging
- `backend/app/ml/segmentation.py` - Segmentation engine (CV + U-Net)
- `backend/app/services/seed_service.py` - Demo data generation
