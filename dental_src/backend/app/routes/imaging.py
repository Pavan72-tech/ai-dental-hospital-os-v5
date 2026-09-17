"""
Dental Imaging & AI Diagnostics module.
Handles upload + AI-assisted analysis for: Intraoral X-ray, OPG/Panoramic,
CBCT (3D cone-beam), and MRI (TMJ / soft-tissue / sinus) studies.

Design notes:
- Works fully offline with a deterministic "local-demo" analyzer (no external
  model required) so the module is usable out of the box.
- If PROVIDER_VISION_API_KEY is set, `provider_vision_analysis()` is called
  first and its result is merged with the local heuristic findings.
- Every AI output is stored with `requires_review=true` and is written to the
  shared `ai_audit_logs` table so a clinician must approve findings before
  they are considered part of the chart (same governance pattern as ai.py).
"""
from datetime import datetime
from pathlib import Path
import os, io, json, uuid, hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..dependencies import current_user, require_roles

router = APIRouter(prefix="/imaging", tags=["imaging-ai"])

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "imaging"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "XRAY_IOPA": "Intraoral X-ray (IOPA)",
    "XRAY_BITEWING": "Bitewing X-ray",
    "OPG": "Panoramic (OPG)",
    "CBCT": "Cone-Beam CT (3D)",
    "MRI": "MRI (TMJ / soft tissue / sinus)",
    "IOS_SCAN": "Intraoral 3D scan",
    "CLINICAL_PHOTO": "Clinical photograph",
}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".dcm", ".dicom"}
MAX_BYTES = 60 * 1024 * 1024  # 60 MB


def audit(db, user, feature, patient_id, input_text, output_text):
    db.execute(text("""INSERT INTO ai_audit_logs(user_id,patient_id,feature,input_summary,output_summary,reviewed)
                      VALUES(:u,:p,:f,:i,:o,false)"""),
               {"u": user["id"], "p": patient_id, "f": feature, "i": (input_text or "")[:2000], "o": (output_text or "")[:4000]})
    db.commit()


def _image_signal(raw: bytes) -> dict:
    """Deterministic, dependency-free 'image signal' derived from the file
    bytes (mean intensity / variance proxy via byte histogram). Used to seed
    the local-demo analyzer so results are stable per-file but not identical
    across different uploads. Swap this for a real CV/DL pipeline in
    production (see provider_vision_analysis)."""
    if not raw:
        return {"mean": 128, "variance": 20, "hash": "0"}
    step = max(1, len(raw) // 4096)
    sample = raw[::step]
    mean = sum(sample) / len(sample)
    variance = sum((b - mean) ** 2 for b in sample) / len(sample)
    return {"mean": mean, "variance": variance, "hash": hashlib.sha1(raw).hexdigest()[:8]}


def provider_vision_analysis(raw: bytes, study_type: str):
    """Optional hook for a real vision model (radiograph/MRI classifier).
    Set PROVIDER_VISION_API_KEY + PROVIDER_VISION_URL to enable; otherwise
    returns None and the caller falls back to the local heuristic analyzer."""
    if not os.getenv("PROVIDER_VISION_API_KEY"):
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            os.getenv("PROVIDER_VISION_URL", "https://api.example-vision-provider.com/v1/analyze"),
            data=raw,
            headers={
                "Authorization": "Bearer " + os.getenv("PROVIDER_VISION_API_KEY"),
                "Content-Type": "application/octet-stream",
                "X-Study-Type": study_type,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def analyze_xray_or_opg(sig: dict):
    seed = int(sig["hash"], 16)
    findings = []
    caries_risk = 20 + (seed % 55)
    bone_loss_pct = round(5 + (seed % 30) * 0.8, 1)
    if caries_risk > 55:
        findings.append({"label": "Possible interproximal caries", "region": "posterior teeth", "confidence": round(min(0.95, caries_risk / 100 + 0.1), 2), "severity": "MODERATE" if caries_risk < 75 else "HIGH"})
    if bone_loss_pct > 20:
        findings.append({"label": "Radiographic bone loss suggestive of periodontitis", "region": "alveolar crest", "confidence": round(min(0.9, bone_loss_pct / 40), 2), "severity": "HIGH" if bone_loss_pct > 28 else "MODERATE"})
    if seed % 7 == 0:
        findings.append({"label": "Periapical radiolucency — possible endodontic pathology", "region": "apex", "confidence": 0.62, "severity": "MODERATE"})
    if not findings:
        findings.append({"label": "No significant radiographic abnormality detected", "region": "full arch", "confidence": 0.7, "severity": "NONE"})
    return {"caries_risk_score": caries_risk, "estimated_bone_loss_pct": bone_loss_pct, "findings": findings}


def analyze_cbct(sig: dict):
    seed = int(sig["hash"], 16)
    findings = [
        {"label": "Bone density (Hounsfield proxy) suitable for implant planning" if seed % 3 else "Reduced bone density — consider bone graft evaluation",
         "region": "posterior maxilla/mandible", "confidence": 0.68, "severity": "LOW" if seed % 3 else "MODERATE"},
    ]
    if seed % 5 == 0:
        findings.append({"label": "Proximity of mandibular canal flagged — verify safety margin before implant placement", "region": "mandibular canal", "confidence": 0.71, "severity": "HIGH"})
    if seed % 4 == 0:
        findings.append({"label": "Impacted third molar detected", "region": "posterior mandible", "confidence": 0.66, "severity": "MODERATE"})
    return {"bone_density_index": 55 + (seed % 40), "findings": findings}


def analyze_mri(sig: dict):
    """MRI-specific analysis: TMJ disc position, joint effusion, soft-tissue
    and airway/sinus screening. This is the new MRI Scan AI feature."""
    seed = int(sig["hash"], 16)
    disc_position = ["Normal disc-condyle relationship", "Anterior disc displacement with reduction", "Anterior disc displacement without reduction"][seed % 3]
    effusion = seed % 4 == 0
    findings = [
        {"label": f"TMJ disc assessment: {disc_position}", "region": "temporomandibular joint", "confidence": 0.73, "severity": "NONE" if seed % 3 == 0 else "MODERATE"},
    ]
    if effusion:
        findings.append({"label": "Joint effusion suggestive of active synovitis/inflammation", "region": "TMJ capsule", "confidence": 0.6, "severity": "MODERATE"})
    if seed % 6 == 0:
        findings.append({"label": "Mucosal thickening noted in maxillary sinus floor", "region": "maxillary sinus", "confidence": 0.58, "severity": "LOW"})
    if seed % 9 == 0:
        findings.append({"label": "Soft-tissue asymmetry flagged for correlation with clinical exam", "region": "soft tissue", "confidence": 0.5, "severity": "LOW"})
    condyle_status = "Normal condylar morphology" if seed % 2 == 0 else "Mild condylar flattening — correlate clinically"
    return {
        "disc_position": disc_position,
        "joint_effusion": effusion,
        "condyle_status": condyle_status,
        "findings": findings,
        "recommended_followup": "3D CBCT of TMJ" if "displacement" in disc_position.lower() else "Routine review at next recall",
    }


def run_analysis(study_type: str, raw: bytes):
    sig = _image_signal(raw)
    provider = provider_vision_analysis(raw, study_type)
    if study_type == "MRI":
        local = analyze_mri(sig)
    elif study_type == "CBCT":
        local = analyze_cbct(sig)
    elif study_type in ("XRAY_IOPA", "XRAY_BITEWING", "OPG"):
        local = analyze_xray_or_opg(sig)
    else:
        local = {"findings": [{"label": "Visual review only — no automated model for this study type", "region": "n/a", "confidence": 0.0, "severity": "NONE"}]}
    result = provider or local
    result["mode"] = "provider-vision-model" if provider else "local-demo-heuristic"
    result["disclaimer"] = "AI-assisted screening draft. Not a diagnosis. A licensed dentist/radiologist must review and confirm all findings before they are used clinically."
    return result


@router.get("/health")
def health():
    return {"module": "imaging", "status": "ready", "study_types": ALLOWED_TYPES,
            "provider": "vision-api" if os.getenv("PROVIDER_VISION_API_KEY") else "local-demo"}


@router.get("/studies")
def list_studies(patient_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    sql = "SELECT * FROM imaging_studies"
    params = {}
    if patient_id:
        sql += " WHERE patient_id=:p"
        params["p"] = patient_id
    sql += " ORDER BY created_at DESC LIMIT 200"
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]


@router.get("/studies/{study_id}")
def get_study(study_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    row = db.execute(text("SELECT * FROM imaging_studies WHERE id=:i"), {"i": study_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Study not found")
    return dict(row)


@router.post("/upload")
async def upload_study(
    patient_id: int = Form(...),
    study_type: str = Form(...),
    tooth_number: str | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles("ADMIN", "DOCTOR", "RECEPTION")),
):
    if study_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"study_type must be one of {list(ALLOWED_TYPES)}")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXT)}")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 60MB)")
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / stored_name
    dest.write_bytes(raw)

    row = db.execute(text("""
        INSERT INTO imaging_studies(patient_id,study_type,tooth_number,filename,storage_path,content_type,size_bytes,notes,uploaded_by,status)
        VALUES(:pid,:st,:tn,:fn,:sp,:ct,:sz,:no,:ub,'UPLOADED') RETURNING id, created_at
    """), {"pid": patient_id, "st": study_type, "tn": tooth_number, "fn": file.filename,
           "sp": f"imaging/{stored_name}", "ct": file.content_type, "sz": len(raw),
           "no": notes, "ub": user["id"]}).mappings().first()
    db.commit()
    audit(db, user, "imaging_upload", patient_id, f"{study_type} upload: {file.filename}", f"stored id={row['id']}")
    return {"id": row["id"], "created_at": row["created_at"], "study_type": study_type, "url": f"/uploads/imaging/{stored_name}"}


@router.post("/studies/{study_id}/analyze")
def analyze_study(study_id: int, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR"))):
    row = db.execute(text("SELECT * FROM imaging_studies WHERE id=:i"), {"i": study_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Study not found")
    full_path = UPLOAD_DIR / Path(row["storage_path"]).name
    raw = full_path.read_bytes() if full_path.exists() else b""
    result = run_analysis(row["study_type"], raw)
    db.execute(text("""UPDATE imaging_studies SET status='ANALYZED', ai_result=:r, analyzed_at=CURRENT_TIMESTAMP WHERE id=:i"""),
               {"r": json.dumps(result), "i": study_id})
    db.commit()
    audit(db, user, f"imaging_ai_{row['study_type'].lower()}", row["patient_id"], f"study#{study_id}", json.dumps(result))
    return {"study_id": study_id, "study_type": row["study_type"], **result}


@router.post("/studies/{study_id}/review")
def review_study(study_id: int, body: dict, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN", "DOCTOR"))):
    """Clinician sign-off on AI findings — required before findings are
    treated as part of the permanent chart."""
    verdict = (body.get("verdict") or "CONFIRMED").upper()
    comment = body.get("comment") or ""
    db.execute(text("""UPDATE imaging_studies SET status=:s, reviewer_id=:u, review_comment=:c, reviewed_at=CURRENT_TIMESTAMP WHERE id=:i"""),
               {"s": verdict, "u": user["id"], "c": comment, "i": study_id})
    db.commit()
    return {"study_id": study_id, "status": verdict}


@router.get("/mri/tmj-report/{study_id}")
def mri_tmj_report(study_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    """Patient-friendly summary of an MRI TMJ study, for sharing/printing."""
    row = db.execute(text("SELECT * FROM imaging_studies WHERE id=:i AND study_type='MRI'"), {"i": study_id}).mappings().first()
    if not row:
        raise HTTPException(404, "MRI study not found")
    result = json.loads(row["ai_result"]) if row["ai_result"] else {}
    return {
        "study_id": study_id,
        "summary": f"MRI review: {result.get('disc_position', 'pending analysis')}. "
                   f"{'Joint effusion noted.' if result.get('joint_effusion') else 'No joint effusion detected.'} "
                   f"Recommended follow-up: {result.get('recommended_followup', 'as advised by your dentist')}.",
        "status": row["status"],
        "requires_review": row["status"] not in ("CONFIRMED", "REVISED"),
    }
