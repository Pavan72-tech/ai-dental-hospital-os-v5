"""
Advanced AI feature set (v2) — extends ai.py with capabilities modern dental
CRMs/PMS are expected to ship in 2026: no-show prediction, an AI treatment
recommender, sentiment analysis on patient messages/reviews, a smart
scheduling optimizer, an insurance/claims assistant, and a WhatsApp/website
virtual receptionist. All endpoints are deterministic "local-demo" logic by
default (no external API key required) and log to ai_audit_logs for
governance, matching the pattern in ai.py / imaging.py.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
import json, re
from ..database import get_db
from ..dependencies import require_roles, current_user

router = APIRouter(prefix="/ai-plus", tags=["ai-advanced"])


def audit(db: Session, user: Any, feature: str, patient_id: Any, input_text: Any, output_text: Any):
    """Safely extracts user ID and writes audit log without crashing the API endpoint."""
    try:
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
        db.execute(
            text("""INSERT INTO ai_audit_logs(user_id,patient_id,feature,input_summary,output_summary,reviewed)
                    VALUES(:u,:p,:f,:i,:o,false)"""),
            {
                "u": user_id, 
                "p": patient_id, 
                "f": feature, 
                "i": str(input_text)[:2000], 
                "o": str(output_text)[:4000]
            }
        )
        db.commit()
    except Exception:
        db.rollback()  # Suppress audit log failure so the endpoint still succeeds


@router.get("/health")
def health():
    return {"module": "ai-plus", "status": "ready", "features": [
        "no-show-prediction", "treatment-recommender", "sentiment-analysis",
        "schedule-optimizer", "insurance-claim-assist", "virtual-receptionist",
        "perio-risk-score", "cross-sell-suggestions"]}


# ---------------------------------------------------------------- No-shows --
@router.post("/no-show-risk")
def no_show_risk(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    """Predicts probability a booked appointment turns into a no-show, from
    signals already in the PMS (history, lead time, channel, distance)."""
    past_no_shows = int(body.get("past_no_shows") or 0)
    total_past = max(1, int(body.get("total_past_appointments") or 1))
    lead_time_days = float(body.get("lead_time_days") or 1)
    is_new_patient = bool(body.get("is_new_patient"))
    booked_via = (body.get("booked_via") or "phone").lower()
    rate = past_no_shows / total_past
    score = 15 + rate * 60
    score += 12 if lead_time_days > 10 else 0
    score += 10 if is_new_patient else 0
    score += 8 if booked_via in ("walk-in-web-form", "online-widget") else 0
    score = round(min(97, score), 1)
    risk = "HIGH" if score >= 60 else "MEDIUM" if score >= 35 else "LOW"
    action = ("Call to reconfirm 24h prior and offer easy reschedule link." if risk == "HIGH" else
              "Send WhatsApp/SMS reminder 24h and 2h before the visit." if risk == "MEDIUM" else
              "Standard automated reminder is sufficient.")
    out = {"no_show_score": score, "risk": risk, "recommended_action": action}
    audit(db, user, "no_show_risk", body.get("patient_id"), body, out)
    return out


# ------------------------------------------------------- Treatment planner --
@router.post("/treatment-recommender")
def treatment_recommender(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR"))):
    """Suggests an evidence-informed treatment sequence/options from a short
    findings list. Always framed as a draft the dentist must confirm."""
    findings = [f.strip().lower() for f in (body.get("findings") or [])]
    plan = []
    if any("caries" in f for f in findings):
        plan.append({"step": "Restorative treatment (composite/GIC) for carious teeth", "priority": 1})
    if any("periodont" in f or "bone loss" in f for f in findings):
        plan.append({"step": "Scaling & root planing, periodontal re-evaluation in 6 weeks", "priority": 1})
    if any("periapical" in f or "endodontic" in f for f in findings):
        plan.append({"step": "Root canal treatment (RCT) referral/booking", "priority": 1})
    if any("impacted" in f for f in findings):
        plan.append({"step": "Oral surgery consult for impacted tooth extraction", "priority": 2})
    if any("tmj" in f or "disc" in f for f in findings):
        plan.append({"step": "Occlusal splint therapy + TMJ physiotherapy referral", "priority": 2})
    if any("implant" in f or "bone density" in f for f in findings):
        plan.append({"step": "Implant planning consult; consider bone graft if density is low", "priority": 3})
    if not plan:
        plan.append({"step": "Routine oral prophylaxis (scaling & polishing) and 6-month recall", "priority": 3})
    out = {"draft_plan": sorted(plan, key=lambda x: x["priority"]),
           "disclaimer": "AI-suggested sequencing only. The treating dentist must confirm diagnosis and plan."}
    audit(db, user, "treatment_recommender", body.get("patient_id"), findings, out)
    return out


# ------------------------------------------------------ Sentiment / reviews --
POS_WORDS = {"great", "excellent", "amazing", "friendly", "painless", "clean", "professional", "happy", "best", "gentle", "recommend"}
NEG_WORDS = {"pain", "rude", "wait", "expensive", "dirty", "worst", "late", "unprofessional", "bad", "hurt", "delay"}

@router.post("/sentiment")
def sentiment(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    text_in = (body.get("text") or "").lower()
    words = re.findall(r"[a-z']+", text_in)
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    score = 50 + (pos - neg) * 12
    score = max(0, min(100, score))
    label = "POSITIVE" if score >= 65 else "NEGATIVE" if score <= 35 else "NEUTRAL"
    flags = []
    if neg >= 2 or "pain" in words or "rude" in words:
        flags.append("Escalate to front-desk manager / complaint queue")
    out = {"sentiment_score": score, "label": label, "flags": flags}
    audit(db, user, "sentiment_analysis", body.get("patient_id"), text_in, out)
    return out


# --------------------------------------------------------- Schedule optimizer --
@router.post("/schedule-optimizer")
def schedule_optimizer(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    """Suggests best slot(s) given chair/doctor utilization + procedure length,
    to reduce gaps and overbooking. Deterministic scoring over provided slots."""
    slots = body.get("candidate_slots") or []
    duration = int(body.get("duration_minutes") or 30)
    scored = []
    for s in slots:
        gap_before = float(s.get("gap_before_minutes", 15))
        gap_after = float(s.get("gap_after_minutes", 15))
        utilization = float(s.get("doctor_utilization_pct", 50))
        fit = 100 - abs(gap_before - duration) * 0.5 - abs(gap_after - duration) * 0.3
        fit += (100 - utilization) * 0.15
        scored.append({**s, "fit_score": round(max(0, min(100, fit)), 1)})
    scored.sort(key=lambda x: -x["fit_score"])
    out = {"ranked_slots": scored[:5], "note": "Higher fit_score = less chair-time waste and lower overlap risk."}
    audit(db, user, "schedule_optimizer", body.get("patient_id"), body, out)
    return out


# --------------------------------------------------------- Insurance / claims --
@router.post("/insurance-claim-assist")
def insurance_claim_assist(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    procedure = (body.get("procedure_code") or body.get("procedure") or "").strip()
    amount = float(body.get("amount") or 0)
    missing = []
    if not body.get("diagnosis_code"):
        missing.append("diagnosis (ICD/CDT) code")
    if not body.get("supporting_xray_id") and not body.get("supporting_notes"):
        missing.append("supporting radiograph or clinical notes")
    if not body.get("pre_authorization") and amount > 25000:
        missing.append("pre-authorization for high-value claim")
    status = "READY_TO_SUBMIT" if not missing else "NEEDS_INFO"
    out = {"status": status, "missing_items": missing,
           "draft_note": f"Claim draft for {procedure or 'procedure'} amounting to {amount}. "
                         f"{'All required documents present.' if not missing else 'Please attach: ' + ', '.join(missing) + '.'}"}
    audit(db, user, "insurance_claim_assist", body.get("patient_id"), body, out)
    return out


# ------------------------------------------------------- Virtual receptionist --
FAQ = {
    "hours": "We are open Monday–Saturday, 9:00 AM to 8:00 PM.",
    "location": "Please share your city/area and we will send the nearest clinic address.",
    "emergency": "For a dental emergency, call the clinic front desk immediately; for severe swelling or trauma, visit the nearest ER.",
    "cost": "Costs vary by treatment. Book a free consultation and we'll share a personalized estimate.",
    "insurance": "We support most major insurance and TPA networks — please share your provider name to confirm coverage.",
}

@router.post("/virtual-receptionist")
def virtual_receptionist(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    msg = (body.get("message") or "").lower()
    intent = "faq"
    reply = None
    for k, v in FAQ.items():
        if k in msg:
            reply = v
            break
    if reply is None:
        if any(w in msg for w in ("book", "appointment", "slot", "schedule")):
            intent = "booking"
            reply = "I can help you book an appointment. Could you share your preferred date/time and the reason for the visit?"
        elif any(w in msg for w in ("pain", "swelling", "bleeding", "broken", "emergency")):
            intent = "emergency_triage"
            reply = "This sounds urgent. We'll prioritize a same-day slot — please call the clinic now or confirm and we will call you back within 10 minutes."
        else:
            intent = "general"
            reply = "Thanks for reaching out! A team member will follow up shortly. Meanwhile, would you like to book a consultation?"
    out = {"intent": intent, "reply": reply, "handoff_to_human": intent == "emergency_triage"}
    audit(db, user, "virtual_receptionist", body.get("patient_id"), msg, out)
    return out


# -------------------------------------------------------------- Perio risk --
@router.post("/perio-risk-score")
def perio_risk_score(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR"))):
    age = int(body.get("age") or 30)
    smoker = bool(body.get("smoker"))
    diabetic = bool(body.get("diabetic"))
    avg_pocket_depth = float(body.get("avg_pocket_depth_mm") or 2.5)
    bleeding_pct = float(body.get("bleeding_on_probing_pct") or 10)
    score = 10 + max(0, age - 30) * 0.4 + avg_pocket_depth * 8 + bleeding_pct * 0.3
    score += 15 if smoker else 0
    score += 15 if diabetic else 0
    score = round(min(100, score), 1)
    risk = "HIGH" if score >= 65 else "MODERATE" if score >= 35 else "LOW"
    out = {"perio_risk_score": score, "risk": risk,
           "recall_interval_months": 3 if risk == "HIGH" else 4 if risk == "MODERATE" else 6}
    audit(db, user, "perio_risk_score", body.get("patient_id"), body, out)
    return out


# ---------------------------------------------------------- Cross-sell/upsell --
@router.post("/cross-sell-suggestions")
def cross_sell_suggestions(body: dict[str, Any], db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION"))):
    """Ethical, need-based suggestions for the front-desk/CRM to raise during
    checkout — never framed as pressure-selling."""
    history = [h.lower() for h in (body.get("treatment_history") or [])]
    age = int(body.get("age") or 30)
    suggestions = []
    if any("cleaning" in h or "scaling" in h for h in history) and age > 25:
        suggestions.append("Offer teeth-whitening consult (common add-on after a cleaning visit).")
    if any("extraction" in h for h in history):
        suggestions.append("Discuss implant or bridge options to restore the extraction site.")
    if any("orthodontic" in h or "aligner" in h for h in history):
        suggestions.append("Recommend a retainer plan and 6-month post-treatment review.")
    if not suggestions:
        suggestions.append("No specific add-on indicated; continue routine preventive care.")
    out = {"suggestions": suggestions, "note": "Present as optional, patient-benefit-first recommendations only."}
    audit(db, user, "cross_sell_suggestions", body.get("patient_id"), body, out)
    return out