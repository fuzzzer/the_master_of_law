# 🚀 Workflow: Deploy Checklist

> **Use when:** Pushing changes to production VPS.
> **Philosophy:** Deployments should be boring. If they're exciting, you're doing it wrong.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `.agents/security_hardener/context.md` for security checks.
Read `PRODUCTION_SETUP.md` for deployment reference.

## Pre-Deploy Verification

### Code Quality
- [ ] All tests pass: `pytest tests/ -q` (expected: 90+ passing)
- [ ] No lint errors or type warnings
- [ ] No `print()` statements (use structured logging)
- [ ] No `APP_ENV=development` hardcoded anywhere
- [ ] `.env.example` updated if new env vars added

### Security
- [ ] No API keys or passwords in committed code
- [ ] No `0.0.0.0` bindings except inside Docker CMD
- [ ] CORS origins restricted to production domain
- [ ] All new endpoints have auth middleware
- [ ] Credit costs assigned to paid endpoints

### Database
- [ ] Alembic migration generated and tested locally
- [ ] Migration is reversible (`alembic downgrade -1` works)
- [ ] No destructive migrations (DROP TABLE, DROP COLUMN) without backup plan

### Deployment Steps
1. SSH to VPS: `ssh -i ~/.ssh/mol_vps deploy@VPS_IP`
2. Pull latest: `cd /var/www/fuzzzy_law && git pull origin main`
3. Check diff: `git log --oneline -5` — verify expected changes
4. Backup DB: `/var/www/fuzzzy_law/scripts/backup-db.sh`
5. Rebuild: `cd backend && docker compose up -d --build`
6. Run migrations: `docker compose exec api alembic upgrade head`
7. Health check: `curl http://localhost:8000/api/v1/health`
8. Smoke test: `curl http://localhost:8000/api/v1/laws/codes`
9. Check logs: `docker compose logs --tail 50 api`
10. External check: `curl https://api.yourdomain.ge/api/v1/health`

### Rollback Plan (if something breaks)
```bash
cd /var/www/fuzzzy_law
git checkout HEAD~1  # Go back one commit
cd backend
docker compose up -d --build
docker compose exec api alembic downgrade -1  # If migration was the problem
```
```
