# Deployment & Cloud Readiness Guide

ORBIT is designed for seamless deployment across local workstations, containerized environments, and Google Cloud Platform.

## 1. Local Quickstart (Zero Configuration)
The application works immediately out of the box using SQLite and deterministic mode without requiring third-party credentials:

### Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## 2. Docker Compose Deployment
Run the complete stack (PostgreSQL 16, FastAPI backend, and Nginx frontend) with one command:
```bash
docker-compose up --build -d
```
Access the application at [http://localhost](http://localhost) (Frontend) and [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive Swagger API documentation).

---

## 3. Google Cloud Platform (GCP) Readiness

### Recommended Architecture:
- **Compute**: Google Cloud Run (Fully managed, auto-scaling container execution for both backend and frontend).
- **Relational Storage**: Cloud SQL for PostgreSQL (Multi-region replica with point-in-time recovery).
- **Observability**: Cloud Logging and Cloud Monitoring with OpenTelemetry exporter.
- **Model Integration**: Vertex AI Gemini API via Google Application Default Credentials (ADC).
- **Secrets**: Google Secret Manager for database credentials.

### Deployment Commands:
```bash
# 1. Build and push backend image to Google Artifact Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/orbit-backend:latest ./backend

# 2. Deploy backend service to Cloud Run
gcloud run deploy orbit-backend \
  --image gcr.io/$PROJECT_ID/orbit-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://orbit_user:password@/orbit_db?host=/cloudsql/$PROJECT_ID:us-central1:orbit-db"

# 3. Build and deploy frontend service to Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/orbit-frontend:latest ./frontend
gcloud run deploy orbit-frontend \
  --image gcr.io/$PROJECT_ID/orbit-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```
