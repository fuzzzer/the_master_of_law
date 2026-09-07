# 🖥 Which VPS to buy — and the 10 one-liners to set it up

> Companion to [`production_preparation.md`](production_preparation.md), which
> has the full detail. This file answers one question: **what to buy, and what
> to run once you have it.**

---

## What the app actually needs (measured, not estimated)

Taken from the stack running locally right now, corpus loaded, 25 hours uptime:

| Container | Memory |
|---|---|
| `api` (FastAPI + ChromaDB) | 237 MB |
| `postgres` | 44 MB |
| `redis` | 10 MB |
| **Total, idle** | **~291 MB** |

Disk: 1.5 GB corpus + ~1.4 GB Docker images + ~3 GB Ubuntu ≈ **7 GB used**.

Under real traffic the API rises well above idle, and the single hungriest
moment is `docker compose build` on the server — compiling the Python image
wants more RAM than serving ever does. Budget for that, not for the idle number.

**Verdict: 4 GB RAM and 40 GB disk is comfortable. You do not need $15/month.**

---

## What to buy

### ✅ Hetzner CX22 — about €4/month

**2 vCPU · 4 GB RAM · 40 GB SSD · 20 TB traffic** *(check current pricing)*

Why this one:

- It is roughly **a quarter of your budget**, with the right shape.
- **Fixed price.** No metered egress, no per-request billing, no autoscaling — nothing that can produce a surprise invoice. This is the real answer to "is billing safe on a machine an AI is operating": the ceiling is the plan, and the plan is the price.
- **Resizes in place.** If traffic justifies it, move to CX32 (4 vCPU / 8 GB / 80 GB, ~€7) from the console without rebuilding anything.
- Your deploy scripts already assume this shape — `backend/deploy.sh` wants an SSH host and `/var/www/fuzzzy_law`.
- Falkenstein or Nuremberg gives decent latency to Georgia.

### For comparison, at your $15 ceiling

| Option | Spec | ~Price | Verdict |
|---|---|---|---|
| **Hetzner CX22** | 2 vCPU / 4 GB / 40 GB | **€4** | ✅ Buy this |
| Hetzner CX32 | 4 vCPU / 8 GB / 80 GB | €7 | Fine if you want headroom now |
| GCP e2-small | 2 vCPU / **2 GB** / disk extra | ~$14 | ❌ 3× the price, half the RAM |
| GCP e2-medium | 2 vCPU / 4 GB | ~$27 | ❌ Over budget |
| DigitalOcean / Vultr | 1–2 vCPU / 2 GB / 50 GB | $12–14 | ❌ 3× the price for less |

**On the GCP credits:** keep them. GCP budgets do not cap spending — they only
send email — so making that account safe means engineering it (trial account
never upgraded, `compute.admin` instead of Owner, CPU quota capped). That is
real work for infrastructure you'd be paying 3× for and migrating off in 90 days
when the credits expire. Spend them on something that benefits from GCP.

### Add-ons

- **Backups: yes** (+20%, ~€0.80). Snapshots of the whole server, independent of the Postgres dumps.
- **Static IPv4:** included.
- **Extra volume:** not yet. Add one only if you expand the corpus.

---

## The 10 one-liners

Steps 1–3 are yours (console and browser). From step 4 on, I can run everything
if you give me the IP.

```bash
# 1 · Create the server — Hetzner console: CX22, Ubuntu 24.04, your SSH key, backups on
# 2 · Point DNS at it — Cloudflare: api.zrdai.work → <NEW_IP>, proxy OFF until TLS works
# 3 · Trust the new host key (the old server's key changed — this is expected)
ssh-keygen -R <NEW_IP> && ssh root@<NEW_IP> 'echo ok'

# 4 · Install Docker
ssh root@<NEW_IP> 'curl -fsSL https://get.docker.com | sh'

# 5 · Clone the repo
ssh root@<NEW_IP> 'git clone https://github.com/fuzzzer/the_master_of_law.git /var/www/fuzzzy_law'

# 6 · Write .env with real secrets  (see production_preparation.md §4.1 — CORS + 4 generated keys)
ssh root@<NEW_IP> 'cd /var/www/fuzzzy_law/backend && cp .env.example .env && nano .env'

# 7 · Ship the corpus — 1.5 GB, and NOTHING ELSE moves it
rsync -avz --progress law_corpus/data/ root@<NEW_IP>:/var/www/fuzzzy_law/law_corpus/data/

# 8 · Start the stack and migrate
ssh root@<NEW_IP> 'cd /var/www/fuzzzy_law/backend && docker compose up -d && docker compose exec -T api alembic upgrade head'

# 9 · TLS via Caddy  (Caddyfile is in .agents/context/production.md §2.2)
ssh root@<NEW_IP> 'docker run -d --name caddy --restart unless-stopped --network host -v /etc/caddy/Caddyfile:/etc/caddy/Caddyfile:ro -v caddy_data:/data caddy:2-alpine'

# 10 · Prove it works
./scripts/smoke-test.sh https://api.zrdai.work
```

Then: nightly backups, and ship the web build.

```bash
ssh root@<NEW_IP> 'echo "0 3 * * * cd /var/www/fuzzzy_law/backend && ./scripts/backup-db.sh >> /var/log/fuzzzy-backup.log 2>&1" | crontab -'
./bump.sh && cd frontend && ./deploy.sh
```

---

## Three things that bite

1. **Step 7 is not optional and fails silently.** The 1.5 GB corpus is git-ignored, so `git clone` does not bring it. A server without it comes up perfectly *healthy* and answers legal questions out of nothing. The only signal is the document count in `/api/v1/health/ready` — which is exactly what step 10 checks.
2. **Keep query strings out of the reverse proxy's access log.** Under BYOK the user's Google API key travels in the WebSocket query string, because browsers cannot set headers on a WS handshake. Log it and you are writing user API keys to disk.
3. **Step 3's host-key warning is expected here.** The old VPS at `49.12.46.185` presents a different key than `known_hosts` has. On a brand-new server, `ssh-keygen -R` is correct. On the *old* IP it would be a red flag — confirm in the console first.

---

## To hand this to me

Give me the IP and confirm your SSH key is on it. I run steps 4–10, plus the
`.env` secrets, the Caddyfile, the cron and the smoke test — and report what
passed. What I cannot do: buy the server, click in a console, or change DNS.
