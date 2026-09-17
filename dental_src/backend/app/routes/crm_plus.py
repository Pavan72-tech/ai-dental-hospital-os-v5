"""
CRM Growth Suite (v2): loyalty & referrals, reputation/review management,
multi-channel campaign automation, and NPS/satisfaction surveys — the pieces
a modern clinic CRM needs beyond basic leads/enquiries (already in crm.py).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
from ..database import get_db
from ..dependencies import current_user, require_roles

router = APIRouter(prefix="/crm-plus", tags=["crm-growth"])


def q(db: Session, sql: str, params: dict = None):
    """Safely executes SELECT queries returning dictionaries."""
    try:
        return [dict(x) for x in db.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        db.rollback()
        return []


def audit(db: Session, user: Any, action: str, entity: str, eid: Any = None):
    """Safely handles audit logging without crashing core CRM functions."""
    try:
        uid = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        db.execute(
            text("INSERT INTO audit_logs(user_id, action, entity, entity_id) VALUES(:u, :a, :e, :i)"),
            {"u": uid, "a": action, "e": entity, "i": eid}
        )
        db.commit()
    except Exception:
        db.rollback()  # Prevent unhandled audit exceptions from crashing the route


@router.get("/health")
def health():
    return {
        "module": "crm-plus", 
        "status": "ready",
        "features": ["loyalty", "referrals", "reviews", "campaigns", "nps-surveys"]
    }


# ------------------------------------------------------------------ Loyalty --
@router.get("/loyalty/{patient_id}")
def loyalty_balance(patient_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        row = db.execute(text("SELECT * FROM loyalty_accounts WHERE patient_id=:p"), {"p": patient_id}).mappings().first()
        if not row:
            db.execute(text("INSERT INTO loyalty_accounts(patient_id,points,tier) VALUES(:p,0,'BRONZE')"), {"p": patient_id})
            db.commit()
            row = db.execute(text("SELECT * FROM loyalty_accounts WHERE patient_id=:p"), {"p": patient_id}).mappings().first()
        history = q(db, "SELECT * FROM loyalty_transactions WHERE patient_id=:p ORDER BY created_at DESC LIMIT 20", {"p": patient_id})
        return {**dict(row or {}), "history": history}
    except Exception:
        db.rollback()
        return {"patient_id": patient_id, "points": 0, "tier": "BRONZE", "history": []}


@router.post("/loyalty/{patient_id}/earn")
def loyalty_earn(patient_id: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION", "DOCTOR"))):
    try:
        points = int(body.get("points") or max(1, int(float(body.get("amount_spent") or 0) // 100)))
        reason = body.get("reason") or "Visit / payment"
        db.execute(text("INSERT INTO loyalty_accounts(patient_id,points,tier) VALUES(:p,0,'BRONZE') ON CONFLICT (patient_id) DO NOTHING"), {"p": patient_id})
        db.execute(text("UPDATE loyalty_accounts SET points=points+:pts WHERE patient_id=:p"), {"pts": points, "p": patient_id})
        
        total = db.execute(text("SELECT points FROM loyalty_accounts WHERE patient_id=:p"), {"p": patient_id}).scalar() or 0
        tier = "PLATINUM" if total >= 2000 else "GOLD" if total >= 800 else "SILVER" if total >= 300 else "BRONZE"
        
        db.execute(text("UPDATE loyalty_accounts SET tier=:t WHERE patient_id=:p"), {"t": tier, "p": patient_id})
        db.execute(text("INSERT INTO loyalty_transactions(patient_id,points,type,reason) VALUES(:p,:pts,'EARN',:r)"), {"p": patient_id, "pts": points, "r": reason})
        db.commit()
        audit(db, user, "loyalty_earn", "patient", patient_id)
        return {"patient_id": patient_id, "points_added": points, "total_points": total, "tier": tier}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error earning loyalty points: {str(e)}")


@router.post("/loyalty/{patient_id}/redeem")
def loyalty_redeem(patient_id: int, body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    try:
        points = int(body.get("points") or 0)
        current = db.execute(text("SELECT points FROM loyalty_accounts WHERE patient_id=:p"), {"p": patient_id}).scalar() or 0
        if points <= 0 or points > current:
            raise HTTPException(400, "Invalid redemption amount")
        
        db.execute(text("UPDATE loyalty_accounts SET points=points-:pts WHERE patient_id=:p"), {"pts": points, "p": patient_id})
        db.execute(text("INSERT INTO loyalty_transactions(patient_id,points,type,reason) VALUES(:p,:pts,'REDEEM',:r)"), {"p": patient_id, "pts": -points, "r": body.get("reason") or "Reward redemption"})
        db.commit()
        audit(db, user, "loyalty_redeem", "patient", patient_id)
        return {"patient_id": patient_id, "redeemed": points, "remaining": current - points}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error redeeming loyalty points: {str(e)}")


# --------------------------------------------------------------- Referrals --
@router.get("/referrals")
def list_referrals(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT * FROM referrals ORDER BY created_at DESC LIMIT 200")


@router.post("/referrals")
def create_referral(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION", "DOCTOR"))):
    try:
        row = db.execute(
            text("""INSERT INTO referrals(referrer_patient_id,referred_name,referred_phone,status,reward_points)
                    VALUES(:rp,:rn,:rph,'PENDING',:pts) RETURNING id"""),
            {
                "rp": body.get("referrer_patient_id"), 
                "rn": body.get("referred_name"),
                "rph": body.get("referred_phone"), 
                "pts": int(body.get("reward_points") or 200)
            }
        ).mappings().first()
        db.commit()
        ref_id = row["id"] if row else None
        audit(db, user, "referral_created", "referral", ref_id)
        return {"id": ref_id, "status": "PENDING"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating referral: {str(e)}")


@router.patch("/referrals/{referral_id}/convert")
def convert_referral(referral_id: int, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    try:
        ref = db.execute(text("SELECT * FROM referrals WHERE id=:i"), {"i": referral_id}).mappings().first()
        if not ref:
            raise HTTPException(404, "Referral not found")
        
        db.execute(text("UPDATE referrals SET status='CONVERTED', converted_at=CURRENT_TIMESTAMP WHERE id=:i"), {"i": referral_id})
        if ref["referrer_patient_id"]:
            db.execute(text("INSERT INTO loyalty_accounts(patient_id,points,tier) VALUES(:p,0,'BRONZE') ON CONFLICT (patient_id) DO NOTHING"), {"p": ref["referrer_patient_id"]})
            db.execute(text("UPDATE loyalty_accounts SET points=points+:pts WHERE patient_id=:p"), {"pts": ref["reward_points"], "p": ref["referrer_patient_id"]})
            db.execute(text("INSERT INTO loyalty_transactions(patient_id,points,type,reason) VALUES(:p,:pts,'EARN','Successful referral')"), {"p": ref["referrer_patient_id"], "pts": ref["reward_points"]})
        
        db.commit()
        audit(db, user, "referral_converted", "referral", referral_id)
        return {"id": referral_id, "status": "CONVERTED", "reward_points": ref["reward_points"]}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error converting referral: {str(e)}")


# ---------------------------------------------------------- Reviews / reputation --
@router.get("/reviews")
def list_reviews(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT * FROM reviews ORDER BY created_at DESC LIMIT 200")


@router.post("/reviews")
def add_review(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        rating = int(body.get("rating") or 5)
        row = db.execute(
            text("""INSERT INTO reviews(patient_id,rating,comment,channel,status)
                    VALUES(:p,:r,:c,:ch,:s) RETURNING id"""),
            {
                "p": body.get("patient_id"), 
                "r": rating, 
                "c": body.get("comment"),
                "ch": body.get("channel") or "IN_APP",
                "s": "NEEDS_RESPONSE" if rating <= 3 else "PUBLISHED"
            }
        ).mappings().first()
        db.commit()
        rev_id = row["id"] if row else None
        return {
            "id": rev_id, 
            "status": "NEEDS_RESPONSE" if rating <= 3 else "PUBLISHED",
            "escalate": rating <= 3
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error submitting review: {str(e)}")


@router.post("/reviews/request")
def request_review(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION", "DOCTOR"))):
    try:
        db.execute(
            text("""INSERT INTO notifications(user_id,patient_id,channel,message)
                    VALUES(:u,:p,:ch,:m)"""),
            {
                "u": None, 
                "p": body.get("patient_id"), 
                "ch": body.get("channel") or "WHATSAPP",
                "m": "Thanks for visiting us! Would you mind leaving a quick Google review? It really helps our clinic. [review link]"
            }
        )
        db.commit()
        return {"status": "queued"}
    except Exception as e:
        db.rollback()
        return {"status": "queued_fallback", "warning": str(e)}


# --------------------------------------------------------------- Campaigns --
@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db), user=Depends(current_user)):
    return q(db, "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 100")


@router.post("/campaigns")
def create_campaign(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    try:
        row = db.execute(
            text("""INSERT INTO campaigns(name,channel,segment,message_template,status)
                    VALUES(:n,:ch,:seg,:msg,'DRAFT') RETURNING id"""),
            {
                "n": body.get("name"), 
                "ch": body.get("channel") or "WHATSAPP",
                "seg": body.get("segment") or "ALL_ACTIVE",
                "msg": body.get("message_template") or ""
            }
        ).mappings().first()
        db.commit()
        c_id = row["id"] if row else None
        audit(db, user, "campaign_created", "campaign", c_id)
        return {"id": c_id, "status": "DRAFT"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creating campaign: {str(e)}")


@router.post("/campaigns/{campaign_id}/launch")
def launch_campaign(campaign_id: int, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "RECEPTION"))):
    try:
        campaign = db.execute(text("SELECT * FROM campaigns WHERE id=:i"), {"i": campaign_id}).mappings().first()
        if not campaign:
            raise HTTPException(404, "Campaign not found")
        
        segment_sql = {
            "ALL_ACTIVE": "SELECT id FROM patients LIMIT 500",
            "OVERDUE_RECALL": "SELECT DISTINCT patient_id AS id FROM recalls WHERE status='DUE' AND due_at<=CURRENT_DATE",
            "HIGH_VALUE": "SELECT DISTINCT patient_id AS id FROM invoices WHERE amount>20000",
        }.get(campaign["segment"], "SELECT id FROM patients LIMIT 500")
        
        targets = [r["id"] for r in q(db, segment_sql)]
        for pid in targets:
            db.execute(text("INSERT INTO campaign_messages(campaign_id,patient_id,status) VALUES(:c,:p,'QUEUED')"), {"c": campaign_id, "p": pid})
            
        db.execute(text("UPDATE campaigns SET status='ACTIVE', launched_at=CURRENT_TIMESTAMP WHERE id=:i"), {"i": campaign_id})
        db.commit()
        audit(db, user, "campaign_launched", "campaign", campaign_id)
        return {"id": campaign_id, "status": "ACTIVE", "targets_queued": len(targets)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error launching campaign: {str(e)}")


# --------------------------------------------------------------- NPS surveys --
@router.post("/nps")
def submit_nps(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    try:
        score = int(body.get("score") or 0)
        category = "PROMOTER" if score >= 9 else "PASSIVE" if score >= 7 else "DETRACTOR"
        row = db.execute(
            text("""INSERT INTO nps_surveys(patient_id,score,category,comment) VALUES(:p,:s,:c,:cm) RETURNING id"""),
            {"p": body.get("patient_id"), "s": score, "c": category, "cm": body.get("comment")}
        ).mappings().first()
        db.commit()
        nps_id = row["id"] if row else None
        return {"id": nps_id, "category": category, "follow_up_required": category == "DETRACTOR"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error submitting NPS survey: {str(e)}")


@router.get("/nps/summary")
def nps_summary(db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    try:
        total = db.execute(text("SELECT count(*) FROM nps_surveys")).scalar() or 0
        if total == 0:
            return {"nps": 0, "total_responses": 0}
        promoters = db.execute(text("SELECT count(*) FROM nps_surveys WHERE category='PROMOTER'")).scalar() or 0
        detractors = db.execute(text("SELECT count(*) FROM nps_surveys WHERE category='DETRACTOR'")).scalar() or 0
        nps = round((promoters - detractors) / total * 100, 1)
        return {"nps": nps, "total_responses": total, "promoters": promoters, "detractors": detractors}
    except Exception:
        db.rollback()
        return {"nps": 0, "total_responses": 0, "promoters": 0, "detractors": 0}