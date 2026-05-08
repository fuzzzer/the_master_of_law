# Specs: Staged Deployment Plan

---

## Behavioral Specifications

### Phase 1: Web

| Aspect | Specification |
|--------|---------------|
| Hosting | VPS (same as backend) via Nginx |
| Domain | `masteroflaw.ge` (or equivalent — confirm with user) |
| SSL | Let's Encrypt via Certbot, auto-renewal |
| CDN | Not required for MVP. Add Cloudflare later if traffic warrants. |
| Build | `flutter build web --release` with `--dart-define=API_URL=https://api.domain` |
| Auth | Firebase Auth (web client ID) |
| Analytics | Firebase Analytics (basic page views, chat usage) |
| Monitoring | Health check cron + Docker logs |
| Rollback | Git-based: `git checkout <previous-tag> && redeploy` |

### Phase 2: Mobile

| Aspect | Android | iOS |
|--------|---------|-----|
| Package | `ge.fuzzycore.masteroflaw` | `ge.fuzzycore.masteroflaw` |
| Min SDK | Android 7.0 (API 24) | iOS 14.0 |
| Build | `flutter build appbundle` | `flutter build ios` |
| Distribution | Google Play | App Store |
| Testing | Internal testing track → Open testing → Production | TestFlight → App Review → Production |
| Crash reporting | Firebase Crashlytics | Firebase Crashlytics |

---

## Technical Constraints

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name masteroflaw.ge;

    ssl_certificate /etc/letsencrypt/live/masteroflaw.ge/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/masteroflaw.ge/privkey.pem;

    root /opt/master-of-law/web;
    index index.html;

    # Flutter web SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /api/v1/chat/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static asset caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
}
```

### Deploy Script Structure

```
scripts/
  deploy-web.sh         — Build Flutter web + rsync to VPS + reload Nginx
  deploy-backend.sh     — Pull latest + rebuild Docker + run migrations
  backup-db.sh          — PostgreSQL backup before deploy
  health-check.sh       — Verify all services are healthy post-deploy
  rollback.sh           — Revert to previous version
```

### Go/No-Go Criteria

**Web launch requires ALL of:**
- [ ] Backend health check returns 200
- [ ] Chat endpoint returns a response within 15s
- [ ] Firebase auth works (register + login)
- [ ] Laws browser loads codes and articles
- [ ] No console errors in browser
- [ ] Privacy policy page accessible
- [ ] SSL grade A or A+ on SSL Labs

**Mobile launch requires ALL of:**
- [ ] Web has been live for ≥ 7 days without critical issues
- [ ] At least 5 feedback submissions received and reviewed
- [ ] All crash-causing bugs fixed
- [ ] Store listing complete (description, screenshots, privacy policy)
- [ ] Internal testing passed by ≥ 3 testers

### Environment Variables (Production)

| Variable | Where Set | Sensitive |
|----------|-----------|-----------|
| `APP_ENV` | `production` | No |
| `DATABASE_URL` | Docker compose | Yes |
| `REDIS_URL` | Docker compose | Yes |
| `CHROMA_HOST` | Docker compose | No |
| `VERTEX_AI_API_KEY` | `.env` | Yes |
| `GOOGLE_CLOUD_PROJECT` | `.env` | No |
| `FIREBASE_SA_KEY_PATH` | Volume mount | Yes |
| `CORS_ORIGINS` | `.env` | No |
| `API_URL` (Flutter) | Build-time `--dart-define` | No |
| `FIREBASE_WEB_CLIENT_ID` | Build-time | No |

### Security Hardening (Production Only)
- No dev mode bypass (Firebase auth enforced)
- Credit system active (no free unlimited)
- Rate limiting enforced
- CORS restricted to `masteroflaw.ge` only
- No debug endpoints exposed
- Secrets never in Git (use `.env` + Docker secrets)
