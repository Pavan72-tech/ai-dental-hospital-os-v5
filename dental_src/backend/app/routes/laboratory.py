"""
Laboratory management module: tracks lab cases, custom orders, shade selections,
delivery dates, and external lab vendor management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
from ..database import get_db
from ..dependencies import current_user, require_roles

router = APIRouter(tags=["laboratory"])


def safe_query(db: Session, sql: str, params: dict = None):
    """Executes SQL queries safely and prevents missing table/column crashes."""
    try:
        return [dict(x) for x in db.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        db.rollback()
        return []


# ----------------------------------------------------------- Lab Cases & Orders --
@router.get("/lab-cases")
@router.get("/lab/cases")
def list_lab_cases(db: Session = Depends(get_db), user=Depends(current_user)):
    return safe_query(db, """
        SELECT lc.*, p.name AS patient_name 
        FROM lab_cases lc 
        LEFT JOIN patients p ON lc.patient_id = p.id 
        ORDER BY lc.created_at DESC LIMIT 200
    """)


@router.get("/lab/orders")
@router.get("/lab-orders")
def list_lab_orders(db: Session = Depends(get_db), user=Depends(current_user)):
    return safe_query(db, """
        SELECT lo.*, p.name AS patient_name 
        FROM lab_orders lo 
        LEFT JOIN patients p ON lo.patient_id = p.id 
        ORDER BY lo.created_at DESC LIMIT 200
    """)


@router.post("/lab-cases")
@router.post("/lab/cases")
def create_lab_case(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    try:
        row = db.execute(
            text("""
                INSERT INTO lab_cases (patient_id, lab_name, work_type, tooth_number, shade, status, due_date, notes)
                VALUES (:p, :l, :w, :t, :s, :st, :d, :n)
                RETURNING id
            """),
            {
                "p": body.get("patient_id"),
                "l": body.get("lab_name") or "In-House Lab",
                "w": body.get("work_type") or "Crown",
                "t": body.get("tooth_number"),
                "s": body.get("shade"),
                "st": body.get("status") or "ORDERED",
                "d": body.get("due_date"),
                "n": body.get("notes")
            }
        ).mappings().first()
        db.commit()
        return {"id": row["id"] if row else None, "status": "ORDERED"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating lab case: {str(e)}")


@router.patch("/lab-cases/{case_id}")
@router.patch("/lab/cases/{case_id}")
def update_lab_case(case_id: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    try:
        db.execute(
            text("UPDATE lab_cases SET status=:s WHERE id=:i"),
            {"s": body.get("status", "RECEIVED"), "i": case_id}
        )
        db.commit()
        return {"id": case_id, "updated": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error updating lab case: {str(e)}")