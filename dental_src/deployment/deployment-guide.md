# Deployment Guide
For demo: open frontend/index.html.
For development backend: `uvicorn app.main:app --reload`.
For infrastructure: use deployment/docker-compose.yml as a starting point.
Production requires secrets management, TLS, backups, monitoring, database migrations and security review.
