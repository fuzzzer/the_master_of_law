# 🔒 Security Hardener — Skill Context

> **When to load:** Deploying to production, reviewing security, hardening infrastructure.

---

## Threat Model for This Project

### Assets to Protect
1. **User conversations** — deeply personal legal situations
2. **GCP credentials** — Vertex AI billing, service account keys
3. **Database** — user data, credit balances, case files
4. **API** — prevent abuse, rate limit enforcement

### Threat Vectors

| Threat | Mitigation | Status |
|--------|-----------|--------|
| SQL Injection | SQLAlchemy ORM (parameterized queries) | ✅ |
| Auth bypass | Firebase token verification middleware | ✅ |
| Credit fraud | Server-side balance check (not client) | ✅ |
| DDoS | Rate limiting per-tier + Caddy/Nginx | ✅ |
| DB exposure | Zero port exposure (Docker internal) | ✅ |
| MITM | TLS via Caddy auto-cert | 🟡 (needs deploy) |
| SA key leak | Mounted read-only, chmod 600 | ✅ |
| CORS bypass | Strict origin whitelist | ✅ |

---

## Security Checklist

### Docker
- [x] PostgreSQL: NO ports mapped
- [x] Redis: NO ports mapped  
- [x] API: bound to `127.0.0.1:8000` only
- [x] `no-new-privileges` on all containers
- [x] `read_only: true` where possible
- [ ] Non-root user in Dockerfile (`USER 1000`)

### Application
- [x] Firebase auth middleware on all routes
- [x] Credit gate checks balance BEFORE processing
- [x] Rate limiting per user tier
- [x] CORS restricted to specific origins
- [x] `scram-sha-256` PostgreSQL auth
- [ ] Request body size limits
- [ ] Input sanitization for Georgian text

### Infrastructure
- [ ] UFW firewall (22, 80, 443 only)
- [ ] Fail2ban for SSH brute-force
- [ ] SSH key-only auth, root disabled
- [ ] Automated backups with offsite copy
- [ ] TLS/HTTPS via Caddy or Certbot
- [ ] Log rotation
- [ ] Secrets rotation schedule

### Dockerfile Hardening
```dockerfile
# Add to Dockerfile for production:
# Run as non-root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1
```

---

## Secret Management Rules

1. **NEVER** commit `.env` to git (it's in `.gitignore`)
2. **NEVER** hardcode API keys in source code
3. **ALWAYS** use `chmod 600` on key files
4. **ROTATE** credentials every 90 days
5. SA key lives at `/etc/fuzzzy-law/gcp-sa-key.json` on VPS (not in repo)
6. Passwords generated via `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
