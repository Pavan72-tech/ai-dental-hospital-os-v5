# AI Dental Hospital OS — Enterprise CRM + AI Upgrade

This package is an upgraded version of the supplied Enterprise v3 project. It keeps the existing backend/database architecture and fixes the frontend startup blocker, wires the AI router, adds working CRM/operations AI actions, and includes local visual assets so the UI does not depend on Google Images.

## Core CRM / Operations covered
- Master patient database + Patient 360
- New enquiry database
- Lead pipeline + assignment
- Appointment tracking
- Consultation / clinical records
- Treatment tracking
- Payment + pending-payment tracking
- Treatment completion workflow foundations
- Doctor database
- Supplier database
- Partner database
- Follow-up tracking
- Dental cleaning recall
- Follow-up recall
- Treatment maintenance / renewal recall
- Patient document checklist
- Patient history / status history
- Complaint tracking
- Escalation workflow
- Daily MIS
- Weekly dashboard
- Monthly dashboard
- Patient conversion dashboard
- Revenue dashboard

## Working AI features
The AI layer works without an external provider using deterministic, auditable demo logic. If `OPENAI_API_KEY` is configured, the clinical drafting endpoints can use the configured provider and otherwise fall back to local demo logic.

- Voice dictation → SOAP draft (browser Speech Recognition where supported)
- Clinical copilot / structured draft
- Patient communication reply draft
- Treatment summary draft
- Lead score + priority
- Follow-up action plan
- Recall priority scoring
- Revenue/operations insight helper
- AI audit logging

Clinical AI outputs are explicitly drafts and require authorized clinician review.

## Visual assets
`frontend/assets/` contains local SVG visual assets and a short MP4 UI loop. Replace these with the clinic's approved photography/videos when available. No Google Images dependency is required.

## Design reference
The information architecture was benchmarked against commonly cited 2026 dental PMS platforms including Dentrix, Open Dental, CareStack, Denticon, Curve Dental, Dentrix Ascend, tab32, Dentrix Enterprise, Eaglesoft and ABELDent. The goal is not to copy their UI, but to combine strong patterns: multi-operatory scheduling, patient 360, clinical charting, treatment/billing continuity, recall, communication, centralized reporting and cloud-ready workflows.

## Run on Windows
1. Ensure PostgreSQL is installed and create the database configured in `backend/.env`.
2. Run the schema/migrations and optional demo seed SQL files in `database/`.
3. Run `RUN-BACKEND-WINDOWS.bat`.
4. Run `RUN-FRONTEND-WINDOWS.bat` in a second terminal.
5. Open `http://127.0.0.1:5500/`.
6. Demo accounts: `admin@demo.local`, `doctor@demo.local`, `reception@demo.local` — password `demo`.

## Important
This is a software demo/starting production codebase, not a certified medical device. Before live clinical deployment, add formal security review, backups/restore testing, encryption/key management, regional privacy compliance, access reviews, monitoring, disaster recovery, validated imaging AI, and clinical governance.
