from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
from ..database import get_db
from ..dependencies import current_user, require_roles

router = APIRouter(prefix="/crm", tags=["crm-operations"])

def q(db, sql, params=None):
    try:
        return [dict(x) for x in db.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        return []

def one(db, sql, params=None):
    try:
        r = db.execute(text(sql), params or {}).mappings().first()
        return dict(r) if r else None
    except Exception:
        return None

def audit(db, user, action, entity, eid=None):
    try:
        db.execute(
            text("INSERT INTO ai_audit_logs(user_id, feature, input_summary, output_summary) VALUES(:u, :f, :i, :o)"),
            {
                "u": user.get("id") if isinstance(user, dict) else getattr(user, "id", None), 
                "f": f"{action}_{entity}", 
                "i": f"entity_id:{eid}", 
                "o": "CRM Action"
            }
        )
        db.commit()
    except Exception:
        db.rollback()

def safe_bind(body: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {k: body.get(k, None) for k in keys}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(current_user)):
    def n(sql, p=None):
        try:
            return db.execute(text(sql), p or {}).scalar() or 0
        except Exception:
            return 0

    def money(sql, p=None):
        try:
            return float(db.execute(text(sql), p or {}).scalar() or 0)
        except Exception:
            return 0.0

    return {
      "patients": int(n("SELECT count(*) FROM patients")),
      "new_enquiries": int(n("SELECT count(*) FROM enquiries WHERE created_at::date=CURRENT_DATE")),
      "open_leads": int(n("SELECT count(*) FROM leads WHERE stage NOT IN ('WON','LOST')")),
      "appointments_today": int(n("SELECT count(*) FROM appointments WHERE starts_at::date=CURRENT_DATE")),
      "completed_today": int(n("SELECT count(*) FROM appointments WHERE starts_at::date=CURRENT_DATE AND status='COMPLETED'")),
      "followups_due": int(n("SELECT count(*) FROM followups WHERE status='PENDING' AND due_at::date<=CURRENT_DATE")),
      "recalls_due": int(n("SELECT count(*) FROM recalls WHERE status='DUE' AND due_at<=CURRENT_DATE")),
      "pending_payments": int(n("SELECT count(*) FROM invoices WHERE amount>paid")),
      "outstanding": money("SELECT coalesce(sum(amount-paid),0) FROM invoices"),
      "revenue_today": money("SELECT coalesce(sum(amount),0) FROM payments WHERE paid_at::date=CURRENT_DATE"),
      "revenue_month": money("SELECT coalesce(sum(amount),0) FROM payments WHERE date_trunc('month',paid_at)=date_trunc('month',CURRENT_DATE)"),
      "treatments_active": int(n("SELECT count(*) FROM treatment_plans WHERE status NOT IN ('COMPLETED','CANCELLED')")),
      "complaints_open": int(n("SELECT count(*) FROM complaints WHERE status<>'CLOSED'")),
      "low_stock": int(n("SELECT count(*) FROM inventory_items WHERE quantity<=reorder_level"))
    }


@router.get("/patient-360/{patient_id}")
def patient_360(patient_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    patient = one(db, "SELECT * FROM patients WHERE id=:p", {"p": patient_id})
    if not patient: 
        raise HTTPException(404, "Patient not found")
    return {
      "patient": patient,
      "appointments": q(db, "SELECT a.*,u.name doctor_name FROM appointments a LEFT JOIN users u ON u.id=a.doctor_id WHERE patient_id=:p ORDER BY starts_at DESC", {"p": patient_id}),
      "visits": q(db, "SELECT v.*,u.name doctor_name FROM clinical_visits v LEFT JOIN users u ON u.id=v.doctor_id WHERE patient_id=:p ORDER BY visit_date DESC", {"p": patient_id}),
      "treatments": q(db, "SELECT * FROM treatment_plans WHERE patient_id=:p ORDER BY id DESC", {"p": patient_id}),
      "invoices": q(db, "SELECT * FROM invoices WHERE patient_id=:p ORDER BY id DESC", {"p": patient_id}),
      "followups": q(db, "SELECT * FROM followups WHERE patient_id=:p ORDER BY due_at DESC", {"p": patient_id}),
      "recalls": q(db, "SELECT * FROM recalls WHERE patient_id=:p ORDER BY due_at DESC", {"p": patient_id}),
      "complaints": q(db, "SELECT * FROM complaints WHERE patient_id=:p ORDER BY created_at DESC", {"p": patient_id}),
      "documents": q(db, "SELECT * FROM patient_documents WHERE patient_id=:p ORDER BY created_at DESC", {"p": patient_id}),
      "checklist": q(db, "SELECT * FROM document_checklists WHERE patient_id=:p ORDER BY id", {"p": patient_id}),
      "status_history": q(db, "SELECT h.*,u.name changed_by_name FROM patient_status_history h LEFT JOIN users u ON u.id=h.changed_by WHERE patient_id=:p ORDER BY created_at DESC", {"p": patient_id})
    }


@router.get("/enquiries")
def enquiries(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT e.*,u.name assigned_name FROM enquiries e LEFT JOIN users u ON u.id=e.assigned_to ORDER BY e.created_at DESC")


@router.post("/enquiries")
def create_enquiry(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    params = safe_bind(body, ["patient_id", "name", "phone", "email", "source", "interest", "stage", "assigned_to", "next_followup", "notes"])
    r = one(db, """INSERT INTO enquiries(patient_id,name,phone,email,source,interest,stage,assigned_to,next_followup,notes)
                   VALUES(:patient_id,:name,:phone,:email,:source,:interest,COALESCE(:stage,'NEW'),:assigned_to,:next_followup,:notes) RETURNING *""", params)
    if not r:
        raise HTTPException(400, "Could not create enquiry")
    db.commit()
    audit(db, user, "CREATE", "enquiry", r["id"])
    return r


@router.patch("/enquiries/{eid}")
def update_enquiry(eid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    allowed = {"name", "phone", "email", "source", "interest", "stage", "assigned_to", "next_followup", "notes", "patient_id"}
    sets = [f"{k}=:{k}" for k in body if k in allowed]
    if not sets: 
        return one(db, "SELECT * FROM enquiries WHERE id=:i", {"i": eid})
    p = {k: v for k, v in body.items() if k in allowed}
    p["i"] = eid
    r = one(db, f"UPDATE enquiries SET {','.join(sets)} WHERE id=:i RETURNING *", p)
    if not r: 
        raise HTTPException(404, "Enquiry not found")
    db.commit()
    audit(db, user, "UPDATE", "enquiry", eid)
    return r


@router.get("/leads")
def leads(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT l.*,u.name assigned_name FROM leads l LEFT JOIN users u ON u.id=l.assigned_to ORDER BY l.created_at DESC")


@router.post("/leads")
def create_lead(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    params = safe_bind(body, ["enquiry_id", "name", "phone", "source", "stage", "assigned_to", "expected_value", "next_followup", "notes"])
    r = one(db, """INSERT INTO leads(enquiry_id,name,phone,source,stage,assigned_to,expected_value,next_followup,notes)
                   VALUES(:enquiry_id,:name,:phone,:source,COALESCE(:stage,'NEW'),:assigned_to,COALESCE(:expected_value,0),:next_followup,:notes) RETURNING *""", params)
    if not r:
        raise HTTPException(400, "Could not create lead")
    db.commit()
    audit(db, user, "CREATE", "lead", r["id"])
    return r


@router.patch("/leads/{lid}")
def update_lead(lid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    allowed = {"stage", "assigned_to", "expected_value", "next_followup", "notes", "name", "phone", "source"}
    sets = [f"{k}=:{k}" for k in body if k in allowed]
    p = {k: v for k, v in body.items() if k in allowed}
    p["i"] = lid
    if not sets: 
        return one(db, "SELECT * FROM leads WHERE id=:i", {"i": lid})
    r = one(db, f"UPDATE leads SET {','.join(sets)} WHERE id=:i RETURNING *", p)
    if not r: 
        raise HTTPException(404, "Lead not found")
    db.commit()
    audit(db, user, "UPDATE", "lead", lid)
    return r


@router.get("/doctors")
def doctors(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT d.*,u.name,u.email,u.role FROM doctors d JOIN users u ON u.id=d.user_id ORDER BY u.name")


@router.post("/doctors")
def create_doctor(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    params = safe_bind(body, ["user_id", "specialization", "registration_no", "phone", "chair", "active"])
    r = one(db, "INSERT INTO doctors(user_id,specialization,registration_no,phone,chair,active) VALUES(:user_id,:specialization,:registration_no,:phone,:chair,COALESCE(:active,true)) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create doctor")
    db.commit()
    audit(db, user, "CREATE", "doctor", r["id"])
    return r


@router.get("/suppliers")
def suppliers(db: Session = Depends(get_db), user=Depends(current_user)): 
    return q(db, "SELECT * FROM suppliers ORDER BY name")


@router.post("/suppliers")
def create_supplier(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    params = safe_bind(body, ["name", "contact_person", "phone", "email", "gstin", "address"])
    r = one(db, "INSERT INTO suppliers(name,contact_person,phone,email,gstin,address) VALUES(:name,:contact_person,:phone,:email,:gstin,:address) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create supplier")
    db.commit()
    audit(db, user, "CREATE", "supplier", r["id"])
    return r


@router.get("/partners")
def partners(db: Session = Depends(get_db), user=Depends(current_user)): 
    return q(db, "SELECT * FROM partners ORDER BY name")


@router.post("/partners")
def create_partner(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    params = safe_bind(body, ["name", "type", "contact_person", "phone", "email", "commission_percent", "notes"])
    r = one(db, "INSERT INTO partners(name,type,contact_person,phone,email,commission_percent,notes) VALUES(:name,:type,:contact_person,:phone,:email,COALESCE(:commission_percent,0),:notes) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create partner")
    db.commit()
    audit(db, user, "CREATE", "partner", r["id"])
    return r


@router.get("/followups")
def followups(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT f.*,p.name patient_name,u.name assigned_name FROM followups f JOIN patients p ON p.id=f.patient_id LEFT JOIN users u ON u.id=f.assigned_to ORDER BY f.due_at")


@router.post("/followups")
def create_followup(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    params = safe_bind(body, ["patient_id", "assigned_to", "type", "due_at", "status", "notes"])
    r = one(db, "INSERT INTO followups(patient_id,assigned_to,type,due_at,status,notes) VALUES(:patient_id,:assigned_to,:type,:due_at,COALESCE(:status,'PENDING'),:notes) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create followup")
    db.commit()
    audit(db, user, "CREATE", "followup", r["id"])
    return r


@router.patch("/followups/{fid}")
def update_followup(fid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    status = body.get("status", "COMPLETED")
    r = one(db, "UPDATE followups SET status=:s,completed_at=CASE WHEN :s='COMPLETED' THEN NOW() ELSE completed_at END,notes=COALESCE(:n,notes) WHERE id=:i RETURNING *", {"s": status, "n": body.get("notes"), "i": fid})
    if not r: 
        raise HTTPException(404, "Follow-up not found")
    db.commit()
    audit(db, user, "UPDATE", "followup", fid)
    return r


@router.get("/recalls")
def recalls(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT r.*,p.name patient_name,p.phone FROM recalls r JOIN patients p ON p.id=r.patient_id ORDER BY r.due_at")


@router.post("/recalls")
def create_recall(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    params = safe_bind(body, ["patient_id", "type", "due_at", "status", "notes"])
    r = one(db, "INSERT INTO recalls(patient_id,type,due_at,status,notes) VALUES(:patient_id,:type,:due_at,COALESCE(:status,'DUE'),:notes) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create recall")
    db.commit()
    audit(db, user, "CREATE", "recall", r["id"])
    return r


@router.patch("/recalls/{rid}")
def update_recall(rid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    s = body.get("status", "COMPLETED")
    r = one(db, "UPDATE recalls SET status=:s,completed_at=CASE WHEN :s='COMPLETED' THEN NOW() ELSE completed_at END,notes=COALESCE(:n,notes) WHERE id=:i RETURNING *", {"s": s, "n": body.get("notes"), "i": rid})
    if not r: 
        raise HTTPException(404, "Recall not found")
    db.commit()
    audit(db, user, "UPDATE", "recall", rid)
    return r


@router.get("/complaints")
def complaints(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT c.*,p.name patient_name,u.name assigned_name FROM complaints c LEFT JOIN patients p ON p.id=c.patient_id LEFT JOIN users u ON u.id=c.assigned_to ORDER BY c.created_at DESC")


@router.post("/complaints")
def create_complaint(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    params = safe_bind(body, ["patient_id", "category", "description", "severity", "status", "assigned_to"])
    r = one(db, "INSERT INTO complaints(patient_id,category,description,severity,status,assigned_to) VALUES(:patient_id,:category,:description,COALESCE(:severity,'MEDIUM'),COALESCE(:status,'OPEN'),:assigned_to) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create complaint")
    db.commit()
    audit(db, user, "CREATE", "complaint", r["id"])
    return r


@router.patch("/complaints/{cid}")
def update_complaint(cid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    r = one(db, "UPDATE complaints SET status=COALESCE(:s,status),resolution=COALESCE(:r,resolution),assigned_to=COALESCE(:a,assigned_to),closed_at=CASE WHEN COALESCE(:s,status)='CLOSED' THEN NOW() ELSE closed_at END WHERE id=:i RETURNING *",
            {"s": body.get("status"), "r": body.get("resolution"), "a": body.get("assigned_to"), "i": cid})
    if not r: 
        raise HTTPException(404, "Complaint not found")
    db.commit()
    audit(db, user, "UPDATE", "complaint", cid)
    return r


@router.get("/document-checklist/{patient_id}")
def checklist(patient_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT * FROM document_checklists WHERE patient_id=:p ORDER BY id", {"p": patient_id})


@router.post("/document-checklist")
def add_checklist(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    params = safe_bind(body, ["patient_id", "document_type", "required", "status", "notes"])
    r = one(db, "INSERT INTO document_checklists(patient_id,document_type,required,status,notes) VALUES(:patient_id,:document_type,COALESCE(:required,true),COALESCE(:status,'PENDING'),:notes) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create document checklist")
    db.commit()
    audit(db, user, "CREATE", "document_checklist", r["id"])
    return r


@router.patch("/patient-status/{patient_id}")
def patient_status(patient_id: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    status = body.get("status", "ACTIVE")
    uid = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    r = one(db, "INSERT INTO patient_status_history(patient_id,status,notes,changed_by) VALUES(:p,:s,:n,:u) RETURNING *", {"p": patient_id, "s": status, "n": body.get("notes"), "u": uid})
    if not r:
        raise HTTPException(400, "Could not update status")
    db.commit()
    audit(db, user, "UPDATE", "patient_status", patient_id)
    return r


@router.get("/status-history/{patient_id}")
def status_history(patient_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT h.*,u.name changed_by_name FROM patient_status_history h LEFT JOIN users u ON u.id=h.changed_by WHERE patient_id=:p ORDER BY created_at DESC", {"p": patient_id})


@router.get("/treatments")
def treatments(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT t.*,p.name patient_name FROM treatment_plans t JOIN patients p ON p.id=t.patient_id ORDER BY t.id DESC")


@router.patch("/treatments/{tid}")
def update_treatment(tid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR"))):
    r = one(db, "UPDATE treatment_plans SET status=COALESCE(:s,status),amount=COALESCE(:a,amount),title=COALESCE(:t,title) WHERE id=:i RETURNING *",
            {"s": body.get("status"), "a": body.get("amount"), "t": body.get("title"), "i": tid})
    if not r: 
        raise HTTPException(404, "Treatment not found")
    db.commit()
    audit(db, user, "UPDATE", "treatment", tid)
    return r


@router.get("/escalations")
def escalations(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT e.*,c.description complaint_description,u.name assigned_name FROM escalations e JOIN complaints c ON c.id=e.complaint_id LEFT JOIN users u ON u.id=e.assigned_to ORDER BY e.created_at DESC")


@router.post("/escalations")
def create_escalation(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    params = safe_bind(body, ["complaint_id", "level", "assigned_to", "reason", "status"])
    r = one(db, "INSERT INTO escalations(complaint_id,level,assigned_to,reason,status) VALUES(:complaint_id,COALESCE(:level,1),:assigned_to,:reason,COALESCE(:status,'OPEN')) RETURNING *", params)
    if not r:
        raise HTTPException(400, "Could not create escalation")
    db.commit()
    audit(db, user, "CREATE", "escalation", r["id"])
    return r


@router.patch("/escalations/{eid}")
def update_escalation(eid: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    r = one(db, "UPDATE escalations SET status=COALESCE(:s,status),level=COALESCE(:l,level),reason=COALESCE(:r,reason),resolved_at=CASE WHEN COALESCE(:s,status)='RESOLVED' THEN NOW() ELSE resolved_at END WHERE id=:i RETURNING *",
            {"s": body.get("status"), "l": body.get("level"), "r": body.get("reason"), "i": eid})
    if not r: 
        raise HTTPException(404, "Escalation not found")
    db.commit()
    audit(db, user, "UPDATE", "escalation", eid)
    return r


@router.get("/mis")
def mis(period: str = "daily", db: Session = Depends(get_db), user=Depends(current_user)):
    period = period.lower()
    start = {"weekly": "CURRENT_DATE-INTERVAL '6 days'", "monthly": "date_trunc('month',CURRENT_DATE)"}.get(period, "CURRENT_DATE")
    try:
        new_p = int(db.execute(text(f"SELECT count(*) FROM patients WHERE created_at::date>={start}")).scalar() or 0)
        appts = int(db.execute(text(f"SELECT count(*) FROM appointments WHERE starts_at::date>={start}")).scalar() or 0)
        comp = int(db.execute(text(f"SELECT count(*) FROM appointments WHERE starts_at::date>={start} AND status='COMPLETED'")).scalar() or 0)
        rev = float(db.execute(text(f"SELECT coalesce(sum(amount),0) FROM payments WHERE paid_at::date>={start}")).scalar() or 0)
        enq = int(db.execute(text(f"SELECT count(*) FROM enquiries WHERE created_at::date>={start}")).scalar() or 0)
        leads_c = int(db.execute(text(f"SELECT count(*) FROM leads WHERE created_at::date>={start}")).scalar() or 0)
        fol_c = int(db.execute(text(f"SELECT count(*) FROM followups WHERE completed_at::date>={start}")).scalar() or 0)
        rec_c = int(db.execute(text(f"SELECT count(*) FROM recalls WHERE completed_at::date>={start} AND status='COMPLETED'")).scalar() or 0)
    except Exception:
        new_p = appts = comp = enq = leads_c = fol_c = rec_c = 0
        rev = 0.0

    return {
      "period": period,
      "new_patients": new_p,
      "appointments": appts,
      "completed": comp,
      "revenue": rev,
      "new_enquiries": enq,
      "new_leads": leads_c,
      "followups_completed": fol_c,
      "recalls_completed": rec_c
    }


@router.get("/conversion")
def conversion(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = q(db, "SELECT stage,count(*) count,coalesce(sum(expected_value),0) value FROM leads GROUP BY stage ORDER BY count DESC")
    total = sum(x["count"] for x in rows)
    won = sum(x["count"] for x in rows if x.get("stage") == "WON")
    return {"stages": rows, "total": total, "won": won, "conversion_rate": round((won / total * 100) if total else 0, 2)}


@router.get("/revenue")
def revenue(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT date_trunc('day',paid_at)::date AS day,coalesce(sum(amount),0) AS revenue,count(*) AS payments FROM payments WHERE paid_at>=CURRENT_DATE-INTERVAL '30 days' GROUP BY 1 ORDER BY 1")


@router.get("/activity")
def activity(db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        return q(db, "SELECT feature as action, input_summary as entity, count(*) count, max(created_at) last_activity FROM ai_audit_logs WHERE created_at>=CURRENT_DATE-INTERVAL '7 days' GROUP BY feature, input_summary ORDER BY last_activity DESC LIMIT 50")
    except Exception:
        return []