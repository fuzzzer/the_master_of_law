# OVH VPS + Cloudflare + Nginx — Fuzzzy Law hosting guide

> The generic OVH/Cloudflare/Nginx walkthrough, rewritten with this project's
> real values and real behaviour. Every port, path, variable and command below
> was taken from the repository as it is — `docker-compose.yml`,
> `.env.example`, `Dockerfile`, the middleware — not from the template's
> placeholders. Where the project's config contradicts the generic guide, the
> project wins and the reason is stated.
>
> Companion documents: [`production_preparation.md`](production_preparation.md)
> (the full reference) · [`vps_choice.md`](vps_choice.md) (sizing, measured).

---

## The final picture

```
Flutter app (web / phone)
      │  HTTPS + WebSocket
      ▼
law-api.fuzzzycore.com    ← Cloudflare DNS, proxied (orange cloud)
      │
      ▼
Cloudflare                ← edge TLS · "Full (strict)" · Always Use HTTPS · WebSockets ON
      │  HTTPS, Origin CA certificate
      ▼
OVH VPS  :443             ← ufw: 22, 80, 443 only
      │
      ▼
nginx                     ← /etc/nginx/sites-available/fuzzzy-law
      │  http://127.0.0.1:8000
      ▼
docker compose            ← /var/www/fuzzzy_law/backend
  ├─ api       127.0.0.1:8000   (FastAPI + ChromaDB, corpus mounted read-only)
  ├─ postgres  internal only    (no published port)
  └─ redis     internal only    (no published port)
```

**The real values used throughout:**

| Placeholder in the generic guide | This project |
|---|---|
| `yourdomain.com` | `fuzzzycore.com` — your domain, already on Cloudflare |
| `api.yourdomain.com` | `law-api.fuzzzycore.com` — set in `frontend/env/env.production` and `nginx.conf.example` |
| `YOUR_SERVER_IP` | the IPv4 OVH gives you; written `<IP>` below |
| `APP_PORT` | **8000** — `docker-compose.yml` binds `127.0.0.1:8000:8000` |
| SSH user | **`ubuntu`** — OVH's default on its Ubuntu image |
| project directory | **`/var/www/fuzzzy_law`** — what `backend/deploy.sh` and `redeploy.sh` expect |
| deployment system | **Docker Compose** — already defined; do not add systemd/PM2 on top |

**The two names, and why they are flat:**

| Purpose | Name | Served by |
|---|---|---|
| Web app | `law.fuzzzycore.com` | Firebase Hosting (project `fuzzzylaws`), Cloudflare **DNS only** |
| API | `law-api.fuzzzycore.com` | OVH via Cloudflare **proxied** |

Not `api.law.fuzzzycore.com`: Cloudflare's free Universal SSL certificate
covers `fuzzzycore.com` and `*.fuzzzycore.com` — **one level deep**. A
two-level name is not on that certificate, so proxied HTTPS to it fails at the
edge unless you pay for Advanced Certificate Manager. `law-api` is one level and
just works.

If you ever change either name, it lives in exactly three places:
`frontend/env/env.production`, `APP_CORS_ORIGINS` in `backend/.env`, and
`server_name` in the nginx file.

---

## Part 1 — Buy the VPS

**OVHcloud → VPS.** Choose:

- **OS:** Ubuntu 24.04 LTS, plain image — no Docker/Plesk/cPanel add-ons. Docker is installed by hand in Part 3 so the version is known.
- **Size:** a tier with **≥ 4 GB RAM and ≥ 40 GB disk**. The stack idles at ~290 MB and uses ~7 GB of disk (measured — see `vps_choice.md`), but `docker compose build` on the server is the hungriest moment and 2 GB tiers fail there.
- **Region:** the closest European datacentre to Georgia (Frankfurt / Warsaw / Strasbourg are all fine).
- **SSH key:** paste your public key during provisioning if OVH offers it (Part 2 shows where it comes from).

Save the IPv4 address OVH gives you. That is `<IP>`.

---

## Part 2 — SSH

On your own computer:

```bash
ls ~/.ssh                 # id_ed25519 + id_ed25519.pub already there?  skip the next line
ssh-keygen -t ed25519     # otherwise: create one, accept the defaults
cat ~/.ssh/id_ed25519.pub # this is the PUBLIC key — safe to give OVH
```

Never share `id_ed25519` without `.pub`. That is the private key.

Connect:

```bash
ssh ubuntu@<IP>
```

First connection asks to trust the host key — for a **brand-new** server, `yes`
is correct. (This is unrelated to the changed-key warning on the old Hetzner
IP `49.12.46.185`; that server is gone and should not be trusted blindly.)

Tell the deploy script about the server — on your computer, in the repo:

```bash
cat > backend/.deploy.env <<EOF
VPS_HOST=<IP>
VPS_USER=ubuntu
VPS_DIR=/var/www/fuzzzy_law
EOF
```

`.deploy.env` is git-ignored.

---

## Part 3 — Base server setup

On the VPS:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx ufw curl git rsync
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
```

Log out and back in so the `docker` group applies, then:

```bash
docker --version && docker compose version
sudo systemctl is-enabled docker nginx     # both must say: enabled
```

`get.docker.com` enables the Docker service on boot; apt enables nginx. Those
two lines are what make Part 12's reboot test pass.

---

## Part 4 — Firewall

```bash
sudo ufw allow OpenSSH      # FIRST, before enabling — or you lock yourself out
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable             # answer y
sudo ufw status
```

Expect exactly `22`, `80`, `443` allowed. **Do not** allow 8000, 5432 or 6379.

**Two project-specific facts about this firewall:**

- **Docker bypasses ufw for published ports.** That is normally a trap. It is harmless here because `docker-compose.yml` publishes the API on **`127.0.0.1:8000` only** and publishes Postgres and Redis **not at all** — there is nothing for Docker to punch through. Keep it that way; never change that `ports:` line to `8000:8000`.
- **Recommended: let only Cloudflare reach 443.** nginx trusts the `CF-Connecting-IP` header for the real client address (Part 8 explains why that matters). If anyone can hit `:443` directly they can set that header themselves. Replacing the open `443` rule with Cloudflare's published ranges closes that:

  ```bash
  sudo ufw delete allow 443/tcp
  for ip in $(curl -s https://www.cloudflare.com/ips-v4) $(curl -s https://www.cloudflare.com/ips-v6); do
    sudo ufw allow from "$ip" to any port 443 proto tcp
  done
  sudo ufw status | grep -c 443     # a couple of dozen rules
  ```

  Keep 80 open to everyone — it only redirects.

---

## Part 5 — Deploy the backend

### 5.1 Clone

```bash
sudo mkdir -p /var/www/fuzzzy_law && sudo chown ubuntu:ubuntu /var/www/fuzzzy_law
git clone https://github.com/fuzzzer/the_master_of_law.git /var/www/fuzzzy_law
cd /var/www/fuzzzy_law/backend
```

### 5.2 `.env` — the real values

```bash
cp .env.example .env
nano .env
```

Change these, and only these. Every other line keeps its default — the
container overrides `APP_ENV`, `AUTH_ENABLED`, `BYOK_REQUIRED` and the internal
DB/Redis URLs itself (see `docker-compose.yml`, `environment:`).

```bash
APP_SECRET_KEY=<paste>        # python3 -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_API_KEY=<paste>         # same generator, a DIFFERENT value
POSTGRES_PASSWORD=<paste>     # same generator
REDIS_PASSWORD=<paste>        # same generator
APP_CORS_ORIGINS=https://law.fuzzzycore.com,https://fuzzzylaw.web.app
```

Why these four secrets are not optional: `Settings` **refuses to start** in
production with the shipped `CHANGE-ME` values (`test_settings_production_guards`
covers it). Why CORS is not `*`: the web app calls the API from another origin
and the app sends identifying headers; a wildcard would let any site do the
same from a visitor's browser. `fuzzzylaw.web.app` is Firebase's default
hostname for the same site; keep it so the app still works if the custom domain
is ever mid-reconfiguration.

Leave `GEMINI_API_KEY` empty. Under `BYOK_REQUIRED=true` every model call is
paid for by the caller's own key; a server key here would quietly serve any
request that lost its caller key on your bill.

### 5.3 The file Docker would otherwise turn into a directory

```bash
echo '{"keys": []}' > api_keys.json
```

`docker-compose.yml` bind-mounts `./api_keys.json`. The file is git-ignored,
so on a fresh clone it does not exist — and Docker "helpfully" creates a
**directory** with that name, which the API then cannot read as JSON.

### 5.4 The corpus — the step that fails silently ⚠️

From **your computer**, in the repo root:

```bash
rsync -avz --progress law_corpus/data/ ubuntu@<IP>:/var/www/fuzzzy_law/law_corpus/data/
```

1.5 GB. `law_corpus/data/` is git-ignored, so the clone did not bring it, and
**nothing else moves it**. A server without it starts perfectly healthy and
answers every legal question out of nothing. The only signal is the document
count in `/api/v1/health/ready` — which Part 10 checks.

`docker-compose.yml` mounts `../law_corpus/data` from the backend directory,
which is why the target path above ends in `/var/www/fuzzzy_law/law_corpus/data/`.

### 5.5 Start and migrate

```bash
cd /var/www/fuzzzy_law/backend
docker compose up -d --build            # first build takes a few minutes
docker compose exec -T api alembic upgrade head
docker compose ps                       # api / postgres / redis all "Up"
```

### 5.6 Test locally — do not continue until this works

```bash
curl -s http://127.0.0.1:8000/api/v1/health
# {"status":"ok","service":"fuzzzy-law","version":"0.1.0"}

curl -s http://127.0.0.1:8000/api/v1/health/ready
# … "detail":"20513 documents across 3 collection(s)" …   ← the corpus is there
```

If `/ready` reports 0 documents, Part 5.4 did not land. Fix that before
touching Cloudflare.

---

## Part 6 — Cloudflare DNS

Cloudflare dashboard → `fuzzzycore.com` → **DNS → Records → Add record**.

**The API record** (this guide's subject):

| Field | Value |
|---|---|
| Type | `A` |
| Name | `law-api` |
| IPv4 | `<IP>` |
| Proxy | **Proxied** (orange cloud) |
| TTL | Auto |

**The web app record** is added in Part 13, because Firebase tells you the
exact values when you register the custom domain — and it must be **DNS only**
(grey cloud), not proxied. Firebase provisions its own certificate for the
custom domain by validating the hostname directly; with Cloudflare's proxy in
front, that validation fails and the site stays on "pending" indefinitely. The
apex `fuzzzycore.com` is already set up this way for your existing site.

---

## Part 7 — Cloudflare Origin certificate

Cloudflare → **SSL/TLS → Origin Server → Create Certificate**. Defaults are fine.
Hostnames: `law-api.fuzzzycore.com` (or `fuzzzycore.com` + `*.fuzzzycore.com`, which covers both names). Create.

Copy **both** values now — the private key is never shown again.

On the VPS:

```bash
sudo mkdir -p /etc/nginx/ssl
sudo nano /etc/nginx/ssl/cloudflare-origin.pem    # paste the Origin Certificate
sudo nano /etc/nginx/ssl/cloudflare-origin.key    # paste the Private Key
sudo chmod 600 /etc/nginx/ssl/cloudflare-origin.key
```

The paths are the ones the project's nginx file already expects.

---

## Part 8 — nginx

The configuration is **in the repository**, already correct for this app:

```bash
sudo cp /var/www/fuzzzy_law/backend/scripts/nginx.conf.example /etc/nginx/sites-available/fuzzzy-law
sudo ln -s /etc/nginx/sites-available/fuzzzy-law /etc/nginx/sites-enabled/fuzzzy-law
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t                # must print: syntax is ok / test is successful
sudo systemctl restart nginx
sudo systemctl status nginx  # active (running)
```

Only edit `server_name` if you chose a domain other than `law-api.fuzzzycore.com`.

**What that file does that the generic template does not — and why:**

| Line | Why it is there |
|---|---|
| `log_format … $uri` instead of `$request` | 🔴 Under BYOK the user's **Google API key travels in the WebSocket query string** (browsers cannot set headers on a WS handshake). The default format logs the full request line — every user's key into `access.log` in plain text. |
| `X-Forwarded-For $http_cf_connecting_ip` (set, not appended) | 🔴 Behind Cloudflare, `$remote_addr` is Cloudflare's edge, not the user. The app hashes the client IP into an **anonymous identity when a device id is missing** (`anonymous_identity.py`) — a wrong or uniform IP merges strangers' cases. Appending would keep any spoofed value the client sent first. |
| `Upgrade` / `Connection $connection_upgrade` + the `map` | The chat runs over `/api/v1/chat/{id}/ws`. Without these the handshake fails with 400. |
| `proxy_read_timeout 300s`, `proxy_buffering off` | A turn runs the full RAG pipeline and can take minutes; the default 60s cut answers off mid-stream. |
| `location /api/` only; `/` → 404 | The API has one public prefix. `/docs` is already disabled in production by `main.py`. |
| `client_max_body_size 10m` | No file uploads exist (`grep UploadFile app/routes/` → nothing); this only bounds JSON. |

And the matching half on the app side, already in `docker-compose.yml`:
`FORWARDED_ALLOW_IPS: "*"`. uvicorn only trusts `X-Forwarded-*` from
`127.0.0.1` by default — but nginx reaches the container from the Docker
gateway (`172.20.0.1`), so without this every request looked like it came from
the gateway. Safe to widen because the port is bound to `127.0.0.1` and only
nginx can reach it.

---

## Part 9 — Cloudflare settings

| Where | Set to |
|---|---|
| SSL/TLS → Overview | **Full (strict)** — never Flexible |
| SSL/TLS → Edge Certificates | **Always Use HTTPS: on** |
| Network | **WebSockets: on** (default, but check — the chat needs it) |

One Cloudflare limit worth knowing: proxied **HTTP** requests time out at the
edge after **100 s** (524). The REST routes `/chat/{id}/send` and `/agent` run
the full pipeline in one request and can approach that; the WebSocket route is
not subject to it, which is one more reason the app's chat uses WS. If you see
524s on `/send`, that is the cause, not the server.

---

## Part 10 — Test everything

On the VPS:

```bash
curl -s http://127.0.0.1:8000/api/v1/health                          # backend
curl -sk https://localhost/api/v1/health -H "Host: law-api.fuzzzycore.com"   # nginx → backend
```

From your computer, in the repo root:

```bash
./scripts/smoke-test.sh https://law-api.fuzzzycore.com
```

Eight checks; expect **8 passed, 0 failed**. It verifies the corpus is mounted,
the law browser works without a key, the BYOK gate rejects keyless model calls
(a 200 there means you are paying for user traffic), and `/docs` is closed.

Then the four things a script cannot check, with a real Google AI Studio key
in the app — listed at the end of the smoke test's output. Item 2, **a second
message on the same open chat**, is the one open question in
`production_preparation.md` §10; check it here.

---

## Part 11 — Backups

```bash
( crontab -l 2>/dev/null; echo "0 3 * * * cd /var/www/fuzzzy_law/backend && ./scripts/backup-db.sh >> /var/log/fuzzzy-backup.log 2>&1" ) | crontab -
./scripts/backup-db.sh            # run one now
./scripts/backup-db.sh --list
```

Dumps go to `/var/backups/fuzzzy-law/`, gzip-verified, 14 days kept. Restore
one **on purpose, once, before launch** with `./scripts/restore-db.sh <dump>`.
Also enable OVH's own snapshot backups in their console — different failure
modes, different tool.

---

## Part 12 — Reboot test

```bash
sudo reboot
```

Reconnect after a minute:

```bash
sudo systemctl status nginx        # active (running)
docker compose -f /var/www/fuzzzy_law/backend/docker-compose.yml ps   # all Up
curl -s https://law-api.fuzzzycore.com/api/v1/health/ready | grep -o '[0-9]* documents'
```

Nothing should need starting by hand: `restart: unless-stopped` on all three
containers, Docker and nginx both enabled.

---

## Part 13 — Ship the frontend

### 13.1 Deploy to Firebase Hosting

On your computer:

```bash
# frontend/env/env.production already says https://law-api.fuzzzycore.com
./bump.sh                      # deploy.sh refuses to ship an unchanged version
cd frontend && ./deploy.sh     # fvm flutter build web → Firebase project "fuzzzylaws"
```

This lands at `https://fuzzzylaw.web.app`. Open it and make one real request
before touching the domain, so a DNS problem later is not mistaken for an app
problem.

### 13.2 Attach `law.fuzzzycore.com`

1. Firebase console → project **fuzzzylaws** → **Hosting → Add custom domain** → `law.fuzzzycore.com`.
2. Firebase shows a TXT record for ownership and then the A records (or a CNAME) for the site. Add them in Cloudflare → `fuzzzycore.com` → DNS, **Proxy: DNS only (grey cloud)** — see Part 6 for why.
3. Wait for Firebase's status to reach **Connected**. Certificate provisioning can take up to a few hours; "Needs setup" or "Pending" for longer than that almost always means the record is proxied.

`APP_CORS_ORIGINS` in Part 5.2 already lists this origin, so no backend change
is needed when the domain goes live.

---

## Part 14 — The project-specific answers, in one table

The generic guide asks the project agent to determine fourteen things. Here
they are.

| # | Question | Answer |
|---|---|---|
| 1 | Deployment command | `docker compose up -d --build` in `/var/www/fuzzzy_law/backend`; updates via `backend/deploy.sh` from your machine |
| 2 | Backend port | `8000`, bound to `127.0.0.1` only |
| 3 | Environment variables | §5.2 — four generated secrets + `APP_CORS_ORIGINS`; everything else defaults; `GEMINI_API_KEY` stays empty |
| 4 | Docker / systemd / PM2 | Docker Compose only. `restart: unless-stopped` on every container. No second supervisor. |
| 5 | Database | Postgres 16 in Compose on the same VPS, **no published port**, `pgdata` named volume. Redis 7 likewise. |
| 6 | nginx | `backend/scripts/nginx.conf.example`, copied verbatim |
| 7 | CORS | `APP_CORS_ORIGINS` — explicit origins, never `*` |
| 8 | WebSockets | Yes: `/api/v1/chat/{id}/ws`. Upgrade headers + 300 s timeout in the nginx file; **API key in the query string ⇒ never log query strings** |
| 9 | Persistent storage | `pgdata` volume · `/var/www/fuzzzy_law/law_corpus/data` (1.5 GB, rsync'd, not in git) · `backend/api_keys.json` |
| 10 | Restart / reboot | Docker + nginx enabled by install; containers `unless-stopped`; verified in Part 12 |
| 11 | Migrations | `docker compose exec -T api alembic upgrade head` — 2 migrations build the full schema from nothing |
| 12 | Health check | `/api/v1/health` (liveness) · `/api/v1/health/ready` (**use this one** — reports the corpus document count) |
| 13 | Production build | Backend: Docker image built on the VPS. Frontend: `fvm flutter build web --release --target lib/main_production.dart` via `deploy.sh` |
| 14 | Directory structure | `/var/www/fuzzzy_law/{backend,frontend,law_corpus,scripts}` — the repo layout, unchanged |

---

## Final checklist

```
[ ] OVH VPS, Ubuntu 24.04, ≥ 4 GB RAM
[ ] SSH key works: ssh ubuntu@<IP>
[ ] backend/.deploy.env written on your machine
[ ] apt upgraded · nginx, ufw, git, rsync, docker installed · ubuntu in docker group
[ ] ufw: 22, 80, 443 only (443 ideally Cloudflare ranges only)
[ ] repo cloned to /var/www/fuzzzy_law
[ ] .env: 4 generated secrets + APP_CORS_ORIGINS · GEMINI_API_KEY empty
[ ] api_keys.json created as a FILE
[ ] corpus rsync'd — /ready shows ~20,513 documents
[ ] docker compose up · alembic upgrade head · all three containers Up
[ ] curl 127.0.0.1:8000/api/v1/health → ok
[ ] Cloudflare A record law-api → <IP>, Proxied
[ ] Origin certificate + key in /etc/nginx/ssl, key chmod 600
[ ] nginx site from nginx.conf.example · nginx -t ok · default site removed
[ ] Cloudflare: Full (strict) · Always Use HTTPS · WebSockets on
[ ] ./scripts/smoke-test.sh https://law-api.fuzzzycore.com → 8 passed
[ ] second message on one open chat works (manual)
[ ] backup cron installed · one dump taken · one restore rehearsed
[ ] reboot test passed
[ ] frontend deployed to fuzzzylaw.web.app · one real request succeeds
[ ] law.fuzzzycore.com attached in Firebase, Cloudflare record DNS-only, status Connected
```
