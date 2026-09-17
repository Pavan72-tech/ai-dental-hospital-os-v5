# AI Dental Hospital OS — Working v2

This package upgrades the original client demo into a locally runnable full-stack development build. It includes authentication/RBAC, live patient CRUD, appointments, clinical visits, prescriptions, billing/payments, inventory/procurement, notifications, patient document upload API, analytics, audit logs and an AI draft endpoint.

## Demo credentials
- admin@demo.local / demo — ADMIN
- doctor@demo.local / demo — DOCTOR
- reception@demo.local / demo — RECEPTION

## Run locally
Backend:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Frontend in a second terminal:
```powershell
cd frontend
& "C:\Users\Pruthviraj\AppData\Local\Programs\Python\Python313\python.exe" -m http.server 5500
```
Open http://localhost:5500 and API docs at http://localhost:8000/docs.

## Important production note
This is a working development foundation, not a claim of regulatory/clinical production compliance. Before real patient data: deploy behind HTTPS, use a managed secrets store, secure object storage, encrypted backups, MFA, rate limiting, CSRF/session policy appropriate to deployment, malware scanning for uploads, immutable audit retention, database migrations, observability, privacy/legal review and clinical validation. AI remains human-review-only.
