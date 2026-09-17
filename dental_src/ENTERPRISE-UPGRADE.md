# AI Dental Hospital OS — Enterprise CRM & Operations Upgrade

This package preserves the original v2 clinical modules and adds a 360-degree clinic operations layer.

## Added
- Master patient database + Patient 360
- Enquiries, leads, stages and lead assignment
- Patient status history
- Doctor, supplier and partner databases
- Follow-up tracking
- Cleaning, follow-up and maintenance/renewal recalls
- Treatment tracking/completion
- Payment/outstanding tracking
- Document checklist
- Complaints and escalation workflow
- Daily MIS, weekly dashboard and monthly dashboard
- Patient conversion dashboard
- Revenue dashboard
- Patient media vault for images and clinical video files
- AI Clinical Copilot with browser voice dictation
- SOAP drafting, patient reply drafting and treatment-summary assistance
- Optional OpenAI-compatible provider integration via environment variables
- Existing v2 modules retained through the legacy module layer

## Start
Backend:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (second terminal):
```powershell
cd frontend
python -m http.server 5500
```

Open http://127.0.0.1:5500/

Demo admin: admin@demo.local / demo

## Optional AI provider
The AI module works in `local-demo` mode without an API key. For real generative drafting, configure:
- OPENAI_API_KEY
- OPENAI_MODEL (optional; defaults to gpt-4.1-mini)

The system treats AI output as draft content and requires human review. Do not use demo AI output as autonomous diagnosis or prescribing.

## Media
Patient records can store PDF, image and common video files. Clinical imaging diagnosis should only be enabled through a validated imaging/AI provider and appropriate clinical governance.
