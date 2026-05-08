# Quick Start Guide

> **Last updated:** 2026-05-09
> **Time to complete:** ~30 minutes
> **Goal:** Backend running on Docker, Flutter app building, first API call succeeding

---

## System Requirements

| Tool | Exact Version | Check Command |
|------|---------------|---------------|
| Python | 3.11+ | `python3 --version` |
| Flutter | 3.32.0+ | `flutter --version` |
| Dart | 3.8.0+ | `dart --version` |
| Docker | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.40+ | `git --version` |

### macOS
```bash
# Install Homebrew if needed: https://brew.sh
brew install python@3.11 docker docker-compose git

# Flutter: download from https://docs.flutter.dev/get-started/install
# Then: flutter doctor
```

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Docker: https://docs.docker.com/engine/install/ubuntu/
# Flutter: https://docs.flutter.dev/get-started/install/linux
```

---

## 1. Clone and Initial Setup

```bash
git clone <repo-url> the_master_of_law
cd the_master_of_law
```

The repository contains three main components:

```
the_master_of_law/
├── backend/          # FastAPI + PostgreSQL + Redis + ChromaDB
├── frontend/         # Flutter app (package: themasteroflaw)
├── law_corpus/       # Pre-built legal corpus (DO NOT MODIFY)
└── eval/             # Evaluation pipeline
```

---

## 2. Backend Setup (Docker)

### 2.1 Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` with these **development** values:

```bash
APP_ENV=development
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# For local dev, set your GCP credentials path:
# GCP_SA_KEY_PATH=~/.config/gcloud/application_default_credentials.json
```

> **Gotcha:** Never commit `.env` to git. It is already in `.gitignore`.

### 2.2 Google Cloud Authentication

The backend uses Vertex AI (Gemini 3.1 Pro + embeddings). You need GCP credentials:

```bash
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install
gcloud auth application-default login
```

This creates `~/.config/gcloud/application_default_credentials.json`.

> **Gotcha:** If you see `GOOGLE_API_KEY` errors later, this step was skipped.

### 2.3 Start Services

```bash
cd backend
docker compose up -d --build
```

This starts three containers:
- `api` — FastAPI on `127.0.0.1:8000`
- `postgres` — PostgreSQL 16 (internal only, no port exposed)
- `redis` — Redis 7 (internal only, no port exposed)

### 2.4 Run Database Migrations

```bash
docker compose exec api alembic upgrade head
```

> **Gotcha:** If migrations fail with "relation does not exist", the PostgreSQL container is still initializing. Wait 10 seconds and retry.

### 2.5 Verify Backend Health

```bash
# Liveness check
curl http://127.0.0.1:8000/api/v1/health
# Expected: {"status":"ok"}

# Readiness check (includes ChromaDB + Vertex AI)
curl http://127.0.0.1:8000/api/v1/health/ready
# Expected: {"status":"ok","components":[...]}
```

If both return `200 OK` with `status: ok`, the backend is running.

---

## 3. Flutter Setup

### 3.1 Install Dependencies

```bash
cd frontend
flutter pub get
```

### 3.2 Run on Emulator or Device

```bash
# List available devices
flutter devices

# Run on the default device
flutter run

# Or specify a device
flutter run -d <device-id>
```

> **Gotcha:** The Flutter package name is `themasteroflaw` (not `master_of_law`). The bundle ID is `ge.fuzzycore.masteroflaw`.

> **Gotcha:** If build fails with "Could not find Dart SDK", run `flutter doctor` and fix any reported issues.

### 3.3 Verify Flutter App

You should see:
- Splash screen with "კანონის ოსტატი" (The Master of Law)
- 5-tab navigation: Chat, Cases, Laws, Notes, Profile
- The app connects to `http://localhost:8000` by default (configurable)

---

## 4. First API Call

### 4.1 Create a Conversation

```bash
curl -X POST http://127.0.0.1:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Consultation"}'
```

Expected response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My First Consultation",
  "phase": "GREETING",
  "legal_domain": "",
  "created_at": "2026-05-09T02:00:00",
  "updated_at": "2026-05-09T02:00:00"
}
```

### 4.2 Send a Chat Message

Replace `{conversation_id}` with the `id` from the previous response:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/{conversation_id}/send \
  -H "Content-Type: application/json" \
  -d '{"message": "ჩემს მეზობელს სახლი დავანგრიე და სასამართლოში მიმყავს. რა უფლებები მაქვს?"}'
```

Expected response (truncated):
```json
{
  "response": "📋 SITUATION SUMMARY...",
  "citations": [...],
  "retrieved_chunks": [...],
  "credits_remaining": 4
}
```

> **Note:** In development mode, no Firebase token is required. The backend uses a mock `ADMIN` user automatically.

### 4.3 Browse Laws (Free, No Credits)

```bash
curl "http://127.0.0.1:8000/api/v1/laws/search?q=მუხლი%2011&top_k=5"
```

---

## 5. Common Errors and Fixes

### `docker compose up` fails with "port already allocated"
```bash
# Something is using port 8000
lsof -i :8000
# Kill the process or change APP_PORT in .env
```

### `alembic upgrade head` fails with connection refused
```bash
# PostgreSQL is still starting
docker compose logs postgres
# Wait for "database system is ready" then retry
```

### ChromaDB telemetry warnings
These appear in logs but are harmless:
```
ERROR:posthog:Unauthorized
```
Ignore them. ChromaDB's telemetry is disabled in production.

### Vertex AI errors ("Permission denied" or "API not enabled")
```bash
# Verify ADC is set up
gcloud auth application-default print-access-token

# Enable Vertex AI API in your GCP project:
# https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
```

### Flutter build fails with "GradleException"
```bash
cd frontend/android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

### Georgian text displays as boxes (□ □ □)
Ensure your terminal/editor supports UTF-8. Georgian uses Mkhedruli script (U+10D0–U+10FF).

---

## 6. Verify Your Setup Checklist

- [ ] `docker compose ps` shows `api`, `postgres`, `redis` as `Up`
- [ ] `curl http://127.0.0.1:8000/api/v1/health` returns `{"status":"ok"}`
- [ ] `curl http://127.0.0.1:8000/api/v1/health/ready` returns `{"status":"ok"}`
- [ ] `curl http://127.0.0.1:8000/api/v1/rag/collections` returns 3 collections with chunk counts
- [ ] `POST /api/v1/conversations` creates a conversation successfully
- [ ] `POST /api/v1/chat/{id}/send` returns an AI response with citations
- [ ] `flutter run` launches the app without errors
- [ ] The Flutter app shows the 5-tab navigation

---

## Next Steps

- **Understand the system:** Read [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- **Build features:** Read [`DEVELOPMENT.md`](./DEVELOPMENT.md)
- **Explore the API:** Read [`API.md`](./API.md)
- **Understand the legal data:** Read [`LAW_CORPUS.md`](./LAW_CORPUS.md)
- **Deploy to production:** Read `.agents/context/production.md` (ops-facing)
