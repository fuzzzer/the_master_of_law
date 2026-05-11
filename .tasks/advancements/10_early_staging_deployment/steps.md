# Deployment & Security Guide: Early Staging on Hetzner + Cloudflare

## Phase 1: VPS Provisioning & Initial Security (Hetzner)
1. **Create VPS:** Provision an Ubuntu 24.04 server in Hetzner Cloud.
2. **Create Non-Root User (on the server as root):**
   ```bash
   adduser fuzzzer
   usermod -aG sudo fuzzzer
   ```
3. **SSH Key Authentication:**
   - **Generate a key on your LOCAL machine** (Mac/Linux/Windows — run locally, not on the server):
     ```bash
     # Check if you already have a key:
     ls ~/.ssh/id_ed25519.pub
     # If not, generate one:
     ssh-keygen -t ed25519 -C "fuzzzer-mac"
     # Press Enter for default path, optionally set a passphrase.
     ```
   - **Copy the public key to the server** (while password auth still works):
     ```bash
     ssh-copy-id fuzzzer@<SERVER_IP>
     ```
   - **Verify key login works** — open a NEW terminal:
     ```bash
     ssh fuzzzer@<SERVER_IP>
     # Should log in WITHOUT asking for a password.
     ```
   - **Repeat for every device** you want SSH access from (each device gets its own key pair).
4. **Disable Root Login & Password Auth (on the server):**
   - ⚠️ Only do this AFTER verifying key login works. Keep your current session open!
   - Edit the SSH config:
     ```bash
     sudo nano /etc/ssh/sshd_config
     ```
   - Find (or add) these lines and set them to:
     ```
     PermitRootLogin no
     PasswordAuthentication no
     ```
   - Also check drop-in overrides:
     ```bash
     cat /etc/ssh/sshd_config.d/*.conf
     # If any file sets PermitRootLogin or PasswordAuthentication, change those too.
     ```
   - Restart SSH:
     ```bash
     sudo systemctl restart sshd
     ```
   - Test again in a NEW terminal before closing anything.
5. **Adding a New Device Later (after password auth is disabled):**
   - On the new device, generate a key: `ssh-keygen -t ed25519 -C "fuzzzer-new-device"`
   - Print the public key: `cat ~/.ssh/id_ed25519.pub`
   - From an already-authorized device, append it to the server:
     ```bash
     ssh fuzzzer@<SERVER_IP> "echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
     ```
   - Alternative: use Hetzner's web Console (Dashboard → Server → Console) to temporarily re-enable password auth.
6. **Configure UFW (Uncomplicated Firewall):**
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   # Verify:
   sudo ufw status
   ```

## Phase 2: DNS & Cloudflare Setup
1. **DNS Records:** In Cloudflare, add an `A` record pointing `masteroflaw.ge` to your Hetzner VPS IP.
2. **Cloudflare Proxy:** Ensure the orange cloud (Proxy status) is turned ON. This hides your origin IP from the public and provides DDoS protection.
3. **SSL/TLS Mode:** Go to Cloudflare SSL/TLS -> Overview, set it to **Full (Strict)**.

## Phase 3: Backend Deployment (Hetzner)

### 3A. Initial Server Setup (one-time)
1. **Install Docker on the server:**
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin
   sudo usermod -aG docker fuzzzer
   # Log out and back in for group to take effect:
   exit
   ssh fuzzzer@<SERVER_IP>
   ```
2. **Clone the repo:**
   ```bash
   sudo mkdir -p /var/www
   sudo chown fuzzzer:fuzzzer /var/www
   cd /var/www
   git clone https://github.com/fuzzzer/the_master_of_law.git
   cd the_master_of_law
   ```

### 3B. Transfer Gitignored Secrets (from Mac)
These files are in `.gitignore` so they must be copied manually via `scp`.

1. **Backend `.env`:**
   ```bash
   scp backend/.env fuzzzer@<SERVER_IP>:/var/www/the_master_of_law/backend/.env
   ```
   Then SSH in and update the production-specific values:
   - `GCP_SA_KEY_PATH=/etc/master-of-law/gcp-sa-key.json`
   - `APP_CORS_ORIGINS` to include your Firebase domain
   - Generate fresh passwords for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `APP_SECRET_KEY`, `ADMIN_API_KEY`

2. **GCP Service Account Key:**
   ```bash
   # On server: create the directory
   ssh fuzzzer@<SERVER_IP> "sudo mkdir -p /etc/master-of-law && sudo chown fuzzzer:fuzzzer /etc/master-of-law"
   # From Mac: copy the key
   scp ~/.config/gcloud/application_default_credentials.json fuzzzer@<SERVER_IP>:/etc/master-of-law/gcp-sa-key.json
   # On server: lock it down
   ssh fuzzzer@<SERVER_IP> "chmod 600 /etc/master-of-law/gcp-sa-key.json"
   ```

3. **Law Corpus Data** (ChromaDB collections):
   ```bash
   # From Mac: sync the law corpus data directory
   rsync -avz --progress law_corpus/data/ fuzzzer@<SERVER_IP>:/var/www/the_master_of_law/law_corpus/data/
   ```

### 3C. First Launch (on server)
```bash
cd /var/www/the_master_of_law/backend
docker compose up -d --build
# Verify:
docker compose ps
docker compose logs -f api
```

### 3D. Server-Side Redeploy Script
Create `/var/www/the_master_of_law/redeploy.sh` on the server:
```bash
#!/bin/bash
cd /var/www/the_master_of_law || exit 1
echo "📥 Pulling latest code..."
git pull origin main
echo "🔨 Rebuilding backend..."
cd backend
docker compose build
docker compose up -d
echo "✅ Redeployed. Checking status..."
docker compose ps
```
Make it executable: `chmod +x /var/www/the_master_of_law/redeploy.sh`

### 3E. Deployment Workflow (from Mac)
Two options — both work:

**Option A: From Mac (automated)** — uses existing scripts:
```bash
./bump.sh    # bumps version, commits, tags, pushes to GitHub
./deploy.sh  # SSHs into server, pulls code, rebuilds containers
```

**Option B: Manual** — when you want more control:
```bash
# On Mac:
git push origin main
# On server (SSH in):
cd /var/www/the_master_of_law && ./redeploy.sh
```

## Phase 4: Nginx & SSL (Backend Proxy)
1. **Install Nginx:**
   ```bash
   sudo apt install nginx
   ```
2. **Configure Nginx:**
   - Create config: `sudo nano /etc/nginx/sites-available/api.zrdai.work`
   - Copy contents from `.tasks/advancements/10_early_staging_deployment/nginx.conf.example`
   - Update `server_name` to `api.zrdai.work`
   - *Note:* Since the frontend is on Firebase, Nginx only serves the API (`/api` and `/ws` paths).
   - Link it: `sudo ln -s /etc/nginx/sites-available/api.zrdai.work /etc/nginx/sites-enabled/`
   - Remove the default: `sudo rm /etc/nginx/sites-enabled/default`
3. **SSL with Cloudflare Origin Certificate** (already created):
   - Certificates are already at `/etc/ssl/cloudflare-origin.pem` and `/etc/ssl/cloudflare-origin-key.pem`
   - Add to your Nginx config:
     ```nginx
     ssl_certificate     /etc/ssl/cloudflare-origin.pem;
     ssl_certificate_key /etc/ssl/cloudflare-origin-key.pem;
     ```
   - Test and restart: `sudo nginx -t && sudo systemctl restart nginx`

## Phase 5: Frontend Deployment (Firebase Hosting)
1. **Initial Setup (First time only):**
   - Open your local terminal in the `frontend/` directory.
   - Run `firebase login` to authenticate.
   - Run `firebase init hosting`.
   - Select your existing Firebase project (`gen-lang-client-0225498420`).
   - For "What do you want to use as your public directory?", type `build/web`.
   - For "Configure as a single-page app?", type `y` (Yes).
   - For "Set up automatic builds and deploys with GitHub?", type `N` (No, we use our own `deploy.sh`).
2. **Deploy:**
   - Run the `./deploy.sh` script from the project root (or `cd frontend && ./deploy.sh`). This automatically runs `flutter build web --release` and `firebase deploy --only hosting`.

## Phase 5: Generating Access Keys
1. Open the deployed application (e.g., `https://masteroflaw.ge`).
2. When prompted for the Staging API Key, enter the exact `ADMIN_API_KEY` string you defined in the backend `.env` file.
3. Once authenticated, you will see a purple Admin Panel floating button in the bottom right corner of the screen.
4. Click the button to automatically generate a secure user `sk_...` key.
5. A dialog will appear. Click "Copy & Close" and distribute this `sk_...` key to your testers.

---

## Analysis of Impenetrability (Security Posture)

### The Defenses
1. **Infrastructure Level (Cloudflare + Hetzner + UFW):**
   - Cloudflare hides the VPS's actual IP address, serving as a shield against direct targeted attacks and mitigating DDoS vectors.
   - UFW ensures that only ports 80 (which immediately redirects to 443), 443 (HTTPS), and 22 (SSH via Keys) are open. The backend FastAPI port (8000) is completely blocked from the outside world.
2. **Network Level (Docker Networks):**
   - The `docker-compose.yml` utilizes an internal bridge network (`mol_internal`).
   - PostgreSQL and Redis have **no ports mapped to the host machine**. It is literally impossible to connect to the database or cache from the public internet; they can only be reached internally by the FastAPI container.
   - FastAPI binds *only* to `127.0.0.1:8000`. Nginx serves as the strict reverse proxy. Bypassing Nginx to hit the API directly is impossible.
3. **Application Level (Temporary Auth System):**
   - **X-API-Key Gateway:** The `FirebaseAuthMiddleware` intercepts every request. If a valid key isn't provided, it rejects the request immediately (401 Unauthorized), completely preventing unauthorized access to the LLM (Gemini 3.1 Pro) APIs or database.
   - **Admin Segregation:** The `SUPERADMIN` tier is exclusively assigned *only* if the incoming key matches the server-side environment variable. Without this exact string, it is cryptographically impossible to trigger the `POST /api/v1/api-keys` endpoint.
   - **Local Storage:** The frontend stores the key securely using `flutter_secure_storage` (which maps to highly secure, encrypted storage mechanisms across platforms: Keychain, Keystore, and encrypted Web storage).

### Potential Vulnerabilities & Mitigation
1. **Leaked User Keys:** Testers might share their `sk_...` keys with unapproved individuals. 
   - *Mitigation:* This is an acceptable risk for early staging. Once the staging phase ends and Firebase Auth is deployed, the `api_keys.json` file will simply be deleted, invalidating all staging access instantly.
2. **Leaked Admin Key:** If the `ADMIN_API_KEY` is leaked, anyone could generate user keys and abuse the API. 
   - *Mitigation:* Treat this key like a production database password. Do not hardcode it in Git; keep it strictly inside the VPS `.env` file.
3. **Origin IP Discovery:** If an attacker finds the real Hetzner IP, they could theoretically bypass Cloudflare and hit Nginx directly. 
   - *Mitigation:* Nginx relies on the `server_name` directive. If traffic hits the IP directly without the `Host` header set to `masteroflaw.ge`, Nginx will drop it. For maximum impenetrability, configure UFW to only allow incoming traffic on ports 80/443 from Cloudflare's officially published IP ranges.

**Conclusion:** 
For an early staging environment, this architecture is exceptionally robust. The separation of concerns (Cloudflare -> Nginx -> FastAPI -> Internal DB) ensures multiple layers of impenetrable walls, and the strict API key middleware provides absolute certainty against unauthorized AI usage and credit draining.
