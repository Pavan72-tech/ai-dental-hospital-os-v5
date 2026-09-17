# System Architecture

Browser / Mobile
→ Frontend
→ Secure API
→ PostgreSQL
→ Encrypted object storage

AI Gateway is isolated from direct unrestricted database access. Clinical AI suggestions require clinician review before becoming official records.

Production target:
Frontend: React/Next.js
Backend: FastAPI/NestJS
Database: PostgreSQL
Cache/queue: Redis
Object storage: S3-compatible
Imaging: DICOM/PACS
Observability: structured logs + monitoring
