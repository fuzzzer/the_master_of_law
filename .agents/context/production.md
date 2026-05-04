# 🚀 Production Environment Setup — The Master of Law

> **From zero to production-ready VPS.** Follow this guide step-by-step.

---

## Prerequisites

| Requirement | Recommended | Minimum |
|-------------|-------------|---------|
| **VPS** | 4 vCPU, 8 GB RAM, 80 GB SSD | 2 vCPU, 4 GB RAM, 40 GB SSD |
| **OS** | Ubuntu 24.04 LTS | Ubuntu 22.04 LTS |
| **Domain** | `kanonis-ostati.ge` or similar | Any domain with DNS control |
| **GCP Account** | Active billing + Vertex AI API enabled | Free trial works initially |
| **Firebase Project** | `gen-lang-client-0225498420` | Any Firebase project |

### VPS Providers (Recommended)
- **Hetzner** (€4-16/mo) — Best price/performance for Europe
- **DigitalOcean** ($12-24/mo) — Simple, great docs
- **Google Cloud Compute** ($15-30/mo) — Same ecosystem, closest to Vertex AI
- **Contabo** (€5-10/mo) — Budget option, adequate for MVP

---

## Phase 1 — VPS Initial Setup

### 1.1 — SSH & Basic Security

```bash
# === ON YOUR LOCAL MACHINE ===

# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "mol-production" -f ~/.ssh/mol_vps

# Copy to VPS (replace with your VPS IP)
ssh-copy-id -i ~/.ssh/mol_vps.pub root@YOUR_VPS_IP

# SSH in
ssh -i ~/.ssh/mol_vps root@YOUR_VPS_IP
```

### 1.2 — Server Hardening

```bash
# === ON THE VPS (as root) ===

# Update system
apt update && apt upgrade -y

# Create deploy user (never run app as root)
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/deploy

# Copy SSH key to deploy user
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Disable root login & password auth
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Fail2ban (brute-force protection)
apt install -y fail2ban
systemctl enable fail2ban
```

> ⚠️ **Test SSH as deploy user in a NEW terminal before closing root session!**
> ```bash
> ssh -i ~/.ssh/mol_vps deploy@YOUR_VPS_IP
> ```

### 1.3 — Install Docker

```bash
# === AS deploy USER ===

# Install Docker Engine (official method)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker deploy

# Log out and back in for group changes
exit
# Re-SSH as deploy

# Verify
docker --version
docker compose version
```

---

## Phase 2 — Domain & TLS

### 2.1 — DNS Configuration

Point your domain to the VPS IP:

```
Type: A
Name: @
Value: YOUR_VPS_IP
TTL: 300

Type: A
Name: api
Value: YOUR_VPS_IP
TTL: 300
```

Wait for DNS propagation (check: `dig api.yourdomain.ge`)

### 2.2 — Caddy Reverse Proxy (Auto-TLS)

Caddy automatically obtains and renews Let's Encrypt certificates.

```bash
# Create Caddy config directory
sudo mkdir -p /etc/caddy

# Create Caddyfile
sudo tee /etc/caddy/Caddyfile << 'EOF'
api.kanonis-ostati.ge {
    reverse_proxy 127.0.0.1:8000

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    # Request size limit (10MB for potential document uploads)
    request_body {
        max_size 10MB
    }

    # Access log
    log {
        output file /var/log/caddy/access.log
        format json
    }
}
EOF

# Run Caddy as Docker container (auto-TLS, zero-config)
docker run -d \
  --name caddy \
  --restart unless-stopped \
  --network host \
  -v /etc/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v caddy_data:/data \
  -v caddy_config:/config \
  -v /var/log/caddy:/var/log/caddy \
  caddy:2-alpine
```

**Alternative: Nginx + Certbot** (if you prefer Nginx):
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo certbot --nginx -d api.kanonis-ostati.ge --email your@email.ge --agree-tos --non-interactive
```

---

## Phase 3 — Deploy The Application

### 3.1 — Clone & Configure

```bash
# Create app directory
sudo mkdir -p /opt/master-of-law
sudo chown deploy:deploy /opt/master-of-law
cd /opt/master-of-law

# Clone repo (or rsync from local)
git clone https://github.com/YOUR_REPO/the_master_of_law.git .
# OR: rsync from local machine
# rsync -avz --exclude='.venv' --exclude='.git' ./ deploy@VPS_IP:/opt/master-of-law/
```

### 3.2 — GCP Service Account Setup

```bash
# Create directory for secrets (not in the repo!)
sudo mkdir -p /etc/master-of-law
sudo chmod 700 /etc/master-of-law
sudo chown deploy:deploy /etc/master-of-law

# === ON YOUR LOCAL MACHINE ===
# Option A: Create a service account (recommended for production)
gcloud iam service-accounts create mol-backend \
  --display-name="Master of Law Backend" \
  --project=gen-lang-client-0225498420

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding gen-lang-client-0225498420 \
  --member="serviceAccount:mol-backend@gen-lang-client-0225498420.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Download key
gcloud iam service-accounts keys create /tmp/mol-sa-key.json \
  --iam-account=mol-backend@gen-lang-client-0225498420.iam.gserviceaccount.com

# Copy to VPS
scp -i ~/.ssh/mol_vps /tmp/mol-sa-key.json deploy@YOUR_VPS_IP:/etc/master-of-law/gcp-sa-key.json

# Secure it
ssh -i ~/.ssh/mol_vps deploy@YOUR_VPS_IP "chmod 600 /etc/master-of-law/gcp-sa-key.json"

# Clean up local copy
rm /tmp/mol-sa-key.json

# Option B: Use ADC (if VPS is a GCP VM — simpler)
# Just assign the VM's service account the roles/aiplatform.user role.
# No key file needed.
```

### 3.3 — Configure Environment

```bash
# === ON THE VPS ===
cd /opt/master-of-law/backend

# Create production .env
cp .env.example .env

# Generate strong passwords
POSTGRES_PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PW=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
APP_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Edit .env with production values
cat > .env << EOF
# ═══ THE MASTER OF LAW — PRODUCTION ═══
APP_NAME=the-master-of-law
APP_ENV=production
APP_PORT=8000
APP_SECRET_KEY=${APP_SECRET}
APP_CORS_ORIGINS=https://kanonis-ostati.ge,https://api.kanonis-ostati.ge

# ── Google Cloud / Vertex AI ──
GOOGLE_CLOUD_PROJECT=gen-lang-client-0225498420
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-3.1-pro
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768

# ── GCP Auth (ADC via mounted service account key) ──
GCP_SA_KEY_PATH=/etc/master-of-law/gcp-sa-key.json

# ── Vector Store ──
CHROMA_PERSIST_DIR=/app/law_corpus_data/chroma

# ── Database ──
POSTGRES_PASSWORD=${POSTGRES_PW}
DATABASE_URL=postgresql+asyncpg://mol_user:${POSTGRES_PW}@postgres:5432/master_of_law
DATABASE_POOL_SIZE=10

# ── Redis ──
REDIS_PASSWORD=${REDIS_PW}
REDIS_URL=redis://:${REDIS_PW}@redis:6379/0

# ── Firebase ──
FIREBASE_PROJECT_ID=gen-lang-client-0225498420

# ── Credits ──
FREE_TIER_DAILY_CREDITS=5
CREDIT_COST_CHAT=1
CREDIT_COST_ANALYSIS=2
CREDIT_COST_CASE_FILE=3

# ── Rate Limits ──
RATE_LIMIT_FREE_PER_MINUTE=5
RATE_LIMIT_PRO_PER_MINUTE=30
RATE_LIMIT_ADMIN_PER_MINUTE=120

# ── Logging ──
LOG_LEVEL=WARNING
EOF

# Lock down the .env file
chmod 600 .env
```

### 3.4 — Launch

```bash
cd /opt/master-of-law/backend

# Build and start all containers
docker compose up -d --build

# Wait for health checks
sleep 30

# Run database migrations
docker compose exec api alembic revision --autogenerate -m "initial"
docker compose exec api alembic upgrade head

# Verify everything is healthy
docker compose ps
# Expected: all 3 containers (api, postgres, redis) showing "healthy" or "Up"

# Test health endpoint
curl http://localhost:8000/api/v1/health
# Expected: {"status": "ok", ...}

# Test through the reverse proxy (TLS)
curl https://api.kanonis-ostati.ge/api/v1/health
# Expected: same response, over HTTPS
```

---

## Phase 4 — Monitoring & Observability

### 4.1 — Application Logs

```bash
# Tail live logs
docker compose logs -f api

# View last 100 lines
docker compose logs --tail 100 api

# Export logs to file (for debugging)
docker compose logs api > /tmp/api-logs-$(date +%Y%m%d).txt
```

### 4.2 — Health Check Monitoring

Create a simple uptime monitor:

```bash
# /opt/master-of-law/scripts/healthcheck.sh
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/v1/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "$(date): HEALTH CHECK FAILED (HTTP $RESPONSE)" >> /var/log/mol-health.log
    # Restart the API container
    cd /opt/master-of-law/backend && docker compose restart api
    # Optional: send notification (webhook, email, Telegram bot)
fi
```

```bash
chmod +x /opt/master-of-law/scripts/healthcheck.sh

# Run every 2 minutes via cron
(crontab -l 2>/dev/null; echo "*/2 * * * * /opt/master-of-law/scripts/healthcheck.sh") | crontab -
```

### 4.3 — External Monitoring (Recommended)

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| **UptimeRobot** | 50 monitors | HTTP uptime checks, 5-min intervals |
| **Better Uptime** | 10 monitors | Status page + incident management |
| **Sentry** | 5k events/mo | Error tracking + performance |

---

## Phase 5 — Backups

### 5.1 — Database Backups

```bash
# /opt/master-of-law/scripts/backup-db.sh
#!/bin/bash
BACKUP_DIR="/opt/master-of-law/backups/db"
mkdir -p $BACKUP_DIR

# Dump PostgreSQL
docker compose -f /opt/master-of-law/backend/docker-compose.yml \
  exec -T postgres pg_dump -U mol_user -d master_of_law \
  | gzip > "$BACKUP_DIR/mol_$(date +%Y%m%d_%H%M%S).sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "$(date): DB backup completed" >> /var/log/mol-backup.log
```

```bash
chmod +x /opt/master-of-law/scripts/backup-db.sh

# Daily backup at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/master-of-law/scripts/backup-db.sh") | crontab -
```

### 5.2 — Offsite Backup (GCS)

```bash
# Install gsutil (if not using a GCP VM)
curl https://sdk.cloud.google.com | bash

# Create backup bucket
gsutil mb -l us-central1 gs://mol-backups-prod

# Sync backups daily (add to cron after the local backup)
gsutil -m rsync -r /opt/master-of-law/backups/ gs://mol-backups-prod/
```

---

## Phase 6 — Updates & Maintenance

### 6.1 — Deploy New Version

```bash
cd /opt/master-of-law

# Pull latest code
git pull origin main

# Rebuild and restart (zero-downtime with health checks)
cd backend
docker compose up -d --build

# Run any new migrations
docker compose exec api alembic upgrade head

# Verify
curl http://localhost:8000/api/v1/health
```

### 6.2 — Rollback

```bash
# If something breaks:
cd /opt/master-of-law
git log --oneline -5        # Find last good commit
git checkout <GOOD_COMMIT>

cd backend
docker compose up -d --build
docker compose exec api alembic downgrade -1  # If migration was the problem
```

### 6.3 — System Updates

```bash
# Monthly: update OS packages
sudo apt update && sudo apt upgrade -y

# Monthly: update Docker images
docker compose pull  # Pulls latest postgres:16-alpine, redis:7-alpine
docker compose up -d

# Check disk usage
df -h
docker system df
docker system prune -f  # Clean unused images/containers
```

---

## Security Checklist

- [ ] SSH: key-only auth, root login disabled
- [ ] UFW firewall: only 22, 80, 443 open
- [ ] Fail2ban installed and active
- [ ] PostgreSQL: zero port exposure, scram-sha-256 auth
- [ ] Redis: zero port exposure, password-protected
- [ ] API: bound to 127.0.0.1 only, behind reverse proxy
- [ ] TLS: auto-managed by Caddy/Certbot, HSTS enabled
- [ ] `.env` file: `chmod 600`, not in git
- [ ] GCP SA key: `chmod 600`, mounted read-only
- [ ] Docker: `no-new-privileges` on all containers
- [ ] Backups: automated daily, offsite copy
- [ ] Monitoring: health checks every 2 minutes
- [ ] CORS: restricted to your domain only

---

## Cost Estimation (Monthly)

| Resource | Provider | Cost |
|----------|----------|------|
| VPS (4 vCPU / 8 GB) | Hetzner | €8-16 |
| Domain (.ge) | Local registrar | ~₾20/year (~€7/year) |
| Vertex AI (Gemini 3.1 Pro) | GCP | $5-50 (usage-dependent) |
| Vertex AI (Embeddings) | GCP | ~$0 (queries only, corpus pre-built) |
| TLS Certificate | Let's Encrypt | Free |
| Monitoring | UptimeRobot | Free |
| **Total** | | **~$15-70/month** |

---

## Quick Reference

```bash
# Start everything
cd /opt/master-of-law/backend && docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f api

# Restart API only
docker compose restart api

# Run migrations
docker compose exec api alembic upgrade head

# Database shell
docker compose exec postgres psql -U mol_user -d master_of_law

# Redis shell
docker compose exec redis redis-cli -a YOUR_REDIS_PASSWORD
```
