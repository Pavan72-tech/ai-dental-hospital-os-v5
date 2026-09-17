import os
import traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text
from .database import engine
from .routes.core import router
from .routes.crm import router as crm_router
from .routes.ai import router as ai_router
from .routes.imaging import router as imaging_router
from .routes.ai_plus import router as ai_plus_router
from .routes.crm_plus import router as crm_plus_router
from .security import hash_password

app = FastAPI(title='AI Dental Hospital OS API', version='2.0.0', docs_url='/docs')

# --------------------------------------------------------------------------
# CORS Middleware
# --------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cors_headers_and_catch_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    except Exception as exc:
        print("\n" + "=" * 50)
        print(f"EXCEPT CAUGHT ON: {request.method} {request.url.path}")
        traceback.print_exc()
        print("=" * 50 + "\n")
        
        return JSONResponse(
            status_code=200,  # Gracefully prevent client network breakdown
            content=[],
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

# --------------------------------------------------------------------------
# Mount Static Files & Sub-Routers
# --------------------------------------------------------------------------
UPLOAD_DIR = Path(__file__).resolve().parents[2] / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount('/uploads', StaticFiles(directory=str(UPLOAD_DIR)), name='uploads')

app.include_router(router)
app.include_router(crm_router)
app.include_router(crm_router, prefix="/crm", tags=["CRM Direct Route"])
app.include_router(ai_router)
app.include_router(imaging_router)
app.include_router(ai_plus_router)
app.include_router(crm_plus_router)

# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class LabCaseCreate(BaseModel):
    patient_id: int
    work_type: str
    lab_name: Optional[str] = "In-House Lab"
    due_date: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = "PENDING"

# --------------------------------------------------------------------------
# Core Database Engine Helper Functions
# --------------------------------------------------------------------------
def fetch_all_lab_cases():
    """Safely queries lab cases without throwing transaction abort errors."""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT l.id, l.patient_id, COALESCE(p.name, 'Patient ' || l.patient_id) AS patient_name, 
                       l.work_type, l.lab_name, l.status, l.due_date, l.instructions, l.created_at
                FROM lab_cases l
                LEFT JOIN patients p ON l.patient_id = p.id
                ORDER BY l.id DESC
            """)
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Primary lab query failed: {e}")

    try:
        with engine.connect() as conn:
            query = text("""
                SELECT id, patient_id, 'Patient ' || patient_id AS patient_name, 
                       work_type, lab_name, status, due_date, instructions, created_at
                FROM lab_cases
                ORDER BY id DESC
            """)
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        print(f"Fallback lab query failed: {e}")

    return []

# --------------------------------------------------------------------------
# GET Endpoints (Matches Network Requests: /lab-cases, /orders, /lab/orders)
# --------------------------------------------------------------------------
@app.get("/lab-cases")
def get_lab_cases_1():
    return fetch_all_lab_cases()

@app.get("/lab/cases")
def get_lab_cases_2():
    return fetch_all_lab_cases()

@app.get("/orders")
def get_orders_1():
    return fetch_all_lab_cases()

@app.get("/lab/orders")
def get_lab_orders_2():
    return fetch_all_lab_cases()

# --------------------------------------------------------------------------
# POST Endpoints
# --------------------------------------------------------------------------
@app.post("/lab-cases")
@app.post("/lab/cases")
def create_lab_case(case: LabCaseCreate):
    try:
        with engine.begin() as conn:
            res = conn.execute(
                text("""
                    INSERT INTO lab_cases (patient_id, work_type, lab_name, due_date, instructions, status)
                    VALUES (:patient_id, :work_type, :lab_name, :due_date, :instructions, :status)
                    RETURNING id, patient_id, work_type, lab_name, due_date, instructions, status, created_at
                """),
                {
                    "patient_id": case.patient_id,
                    "work_type": case.work_type,
                    "lab_name": case.lab_name,
                    "due_date": case.due_date,
                    "instructions": case.instructions,
                    "status": case.status
                }
            )
            row = res.fetchone()
            return dict(row._mapping) if row else {"status": "created"}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})

# --------------------------------------------------------------------------
# Schema Migration Guard
# --------------------------------------------------------------------------
DDL = '''
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lab_cases (
    id SERIAL PRIMARY KEY,
    patient_id INT,
    work_type VARCHAR(200) DEFAULT 'General',
    lab_name VARCHAR(200) DEFAULT 'In-House Lab',
    due_date DATE,
    instructions TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

@app.on_event('startup')
def startup():
    try:
        with engine.begin() as c:
            for stmt in DDL.split(';'):
                if stmt.strip():
                    try:
                        c.execute(text(stmt))
                    except Exception as e:
                        print(f"Schema setup note: {e}")
    except Exception as e:
        print(f"Database connection issue during startup: {e}")

@app.get('/health')
def health(): 
    return {'status': 'ok', 'version': '2.0.0'}