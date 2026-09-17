from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any
import os, json, urllib.request
from ..database import get_db
from ..dependencies import require_roles

router=APIRouter(prefix="/ai",tags=["ai"])

def audit(db,user,feature,patient_id,input_text,output_text):
    db.execute(text("""INSERT INTO ai_audit_logs(user_id,patient_id,feature,input_summary,output_summary,reviewed)
                      VALUES(:u,:p,:f,:i,:o,false)"""),
               {"u":user["id"],"p":patient_id,"f":feature,"i":input_text[:2000],"o":output_text[:4000]})
    db.commit()

def local_ai(prompt, context=""):
    p=(prompt or "").lower()
    if "soap" in p or "clinical note" in p:
        return ("S — Subjective:\n• Chief complaint and patient-reported symptoms: [review and complete]\n\n"
                "O — Objective:\n• Clinical examination findings: [review and complete]\n• Imaging/tests: [review and complete]\n\n"
                "A — Assessment:\n• [Clinician to enter/verify diagnosis]\n\n"
                "P — Plan:\n• [Clinician to enter/verify treatment plan]\n• Follow-up: [enter interval]\n\n"
                "AI DRAFT — clinician review and approval required before saving.")
    if "follow" in p or "recall" in p:
        return "Suggested workflow: contact patient, confirm reason for follow-up/recall, offer suitable appointment slots, document outcome, and schedule the next recall. AI-generated draft; staff approval required."
    if "reply" in p or "whatsapp" in p or "message" in p:
        return "Hello, thank you for contacting the clinic. We have noted your request and our team will help you with the next available appointment. Please confirm your preferred date and time. — Clinic Team"
    if "summary" in p:
        return "Patient/visit summary draft based on supplied context:\n" + context[:2500] + "\n\nAI DRAFT — verify against the clinical record."
    return "AI assistant draft:\n\n" + (prompt or "") + "\n\nRecommended next step: review the patient's record, verify facts, and have an authorized clinician approve any clinical content."

def provider_ai(prompt, context=""):
    key=os.getenv("OPENAI_API_KEY")
    if not key: return None
    model=os.getenv("OPENAI_MODEL","gpt-4.1-mini")
    payload=json.dumps({"model":model,"messages":[
        {"role":"system","content":"You are a dental-clinic workflow assistant. Draft only. Never make an autonomous diagnosis, prescribe, or replace a dentist. Clearly label uncertainty and require clinician review."},
        {"role":"user","content":"Context:\n"+context[:6000]+"\n\nRequest:\n"+prompt[:6000]}
    ],"temperature":0.2}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=payload,headers={"Content-Type":"application/json","Authorization":"Bearer "+key},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            data=json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None

@router.get("/health")
def health():
    return {"module":"ai","status":"ready","provider":"openai-compatible" if os.getenv("OPENAI_API_KEY") else "local-demo","voice":"browser-speech-api"}

@router.post("/draft")
def draft(body:dict[str,Any],db:Session=Depends(get_db),user=Depends(require_roles("ADMIN","DOCTOR"))):
    patient=None
    if body.get("patient_id"):
        patient=db.execute(text("SELECT name,medical_history FROM patients WHERE id=:p"),{"p":body["patient_id"]}).mappings().first()
    context=("Patient: "+patient["name"]+"\nMedical history: "+(patient["medical_history"] or "not provided")) if patient else ""
    out=provider_ai(body.get("prompt",""),context) or local_ai(body.get("prompt",""),context)
    audit(db,user,"clinical_draft",body.get("patient_id"),body.get("prompt",""),out)
    return {"draft":out,"mode":"provider" if os.getenv("OPENAI_API_KEY") else "local-demo","requires_review":True}

@router.post("/soap")
def soap(body:dict[str,Any],db:Session=Depends(get_db),user=Depends(require_roles("ADMIN","DOCTOR"))):
    body["prompt"]="Create a SOAP clinical note draft from this dictation: "+body.get("dictation","")
    return draft(body,db,user)

@router.post("/reply")
def reply(body:dict[str,Any],db:Session=Depends(get_db),user=Depends(require_roles("ADMIN","RECEPTION","DOCTOR"))):
    body["prompt"]="Draft a concise patient communication reply: "+body.get("message","")
    return draft(body,db,user)

@router.post("/treatment-summary")
def treatment_summary(body:dict[str,Any],db:Session=Depends(get_db),user=Depends(require_roles("ADMIN","DOCTOR"))):
    body["prompt"]="Create a patient-friendly treatment summary and questions the dentist should verify: "+body.get("prompt","")
    return draft(body,db,user)

@router.post('/lead-score')
def lead_score(body:dict[str,Any], db:Session=Depends(get_db), user=Depends(require_roles('ADMIN','DOCTOR','RECEPTION'))):
    """Deterministic demo scoring: useful even without an external LLM."""
    value=float(body.get('expected_value') or 0); stage=(body.get('stage') or 'NEW').upper(); source=(body.get('source') or '').lower()
    score=35
    score += min(30, int(value/10000))
    score += {'CONTACTED':10,'CONSULTATION':18,'TREATMENT_PROPOSED':25,'WON':30}.get(stage,0)
    score += 8 if source in {'referral','doctor','existing patient'} else 0
    score=min(100,score)
    priority='HIGH' if score>=75 else 'MEDIUM' if score>=50 else 'LOW'
    recommendation='Call within 15 minutes and offer two consultation slots.' if priority=='HIGH' else 'Follow up today and personalize the message.' if priority=='MEDIUM' else 'Add to nurture queue and follow up within 48 hours.'
    out={'score':score,'priority':priority,'recommendation':recommendation,'factors':['stage','expected treatment value','lead source']}
    audit(db,user,'lead_score',None,str(body),json.dumps(out)); return out

@router.post('/followup-plan')
def followup_plan(body:dict[str,Any], db:Session=Depends(get_db), user=Depends(require_roles('ADMIN','DOCTOR','RECEPTION'))):
    status=(body.get('status') or 'PENDING').upper(); typ=(body.get('type') or 'FOLLOW-UP').replace('_',' ').title(); notes=body.get('notes') or ''
    if status=='COMPLETED': next_step='Thank the patient, document outcome, and schedule the next clinical or recall date.'
    else: next_step=f'Contact the patient about {typ.lower()}, confirm the reason for the visit, offer available slots, and record the outcome.'
    out={'priority':'HIGH' if 'payment' in typ.lower() or 'complaint' in typ.lower() else 'NORMAL','next_step':next_step,'message':f'Hello, we are following up regarding your {typ.lower()}. Please let us know a convenient time for your next step.','checklist':['Verify patient identity','Review latest record','Contact patient','Document outcome','Schedule next action']}
    audit(db,user,'followup_plan',body.get('patient_id'),str(body),json.dumps(out)); return out

@router.post('/recall-priority')
def recall_priority(body:dict[str,Any], db:Session=Depends(get_db), user=Depends(require_roles('ADMIN','DOCTOR','RECEPTION'))):
    typ=(body.get('type') or 'Recall').lower(); days=int(body.get('days_overdue') or 0)
    score=min(100,40+max(0,days)*4+(20 if 'clean' in typ else 10 if 'maintenance' in typ else 0))
    out={'score':score,'priority':'HIGH' if score>=75 else 'MEDIUM' if score>=50 else 'LOW','reason':f'{max(days,0)} day(s) overdue; recall type is {typ}.','suggested_action':'Call + WhatsApp draft' if score>=75 else 'WhatsApp/SMS reminder' if score>=50 else 'Automated reminder queue'}
    audit(db,user,'recall_priority',body.get('patient_id'),str(body),json.dumps(out)); return out

@router.post('/revenue-insights')
def revenue_insights(body:dict[str,Any], db:Session=Depends(get_db), user=Depends(require_roles('ADMIN'))):
    revenue=float(body.get('revenue') or 0); outstanding=float(body.get('outstanding') or 0); conversion=float(body.get('conversion_rate') or 0)
    actions=[]
    if outstanding>revenue*0.25: actions.append('Prioritize pending-payment follow-up queue.')
    if conversion<35: actions.append('Review enquiry response time and consultation-to-treatment conversion.')
    if not actions: actions.append('Metrics are within the demo thresholds; continue monitoring weekly.')
    out={'health':'WATCH' if len(actions)>1 else 'STABLE','actions':actions,'note':'Operational decision support only; validate against accounting and management reports.'}
    audit(db,user,'revenue_insights',None,str(body),json.dumps(out)); return out
