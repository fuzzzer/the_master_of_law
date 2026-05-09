# Deployment & Security Guide: Early Staging on Hetzner + Cloudflare

## Phase 1: VPS Provisioning & Initial Security (Hetzner)
1. **Create VPS:** Provision an Ubuntu 24.04 server in Hetzner Cloud.
2. **Initial Server Security:**
   - Create a non-root user (e.g., `fuzzzer`).
   - Setup SSH key authentication for `fuzzzer` and disable root login.
   - Disable password authentication in `/etc/ssh/sshd_config` (`PasswordAuthentication no`).
   - Configure UFW (Uncomplicated Firewall):
     - `sudo ufw allow OpenSSH`
     - `sudo ufw allow 80/tcp`
     - `sudo ufw allow 443/tcp`
     - `sudo ufw enable`

## Phase 2: DNS & Cloudflare Setup
1. **DNS Records:** In Cloudflare, add an `A` record pointing `masteroflaw.ge` to your Hetzner VPS IP.
2. **Cloudflare Proxy:** Ensure the orange cloud (Proxy status) is turned ON. This hides your origin IP from the public and provides DDoS protection.
3. **SSL/TLS Mode:** Go to Cloudflare SSL/TLS -> Overview, set it to **Full (Strict)**.

## Phase 3: Backend Deployment (Hetzner)
1. **Clone & Setup:** Clone the repository on the VPS.
2. **Backend Configuration:**
   - Create the `.env` file from `.env.example` in the `backend/` directory.
   - Update `APP_CORS_ORIGINS` to include your Firebase domain (e.g., `https://the-master-of-law.web.app`).
   - Set `ADMIN_API_KEY` to a strong, random secret.
   - Run `docker compose up -d --build`. This starts FastAPI, PostgreSQL, and Redis within the secure internal Docker network.

## Phase 4: Nginx & SSL (Backend Proxy)
1. **Install Nginx:** `sudo apt install nginx`.
2. **Configure Nginx:** 
   - Create a configuration file: `sudo nano /etc/nginx/sites-available/masteroflaw.ge`.
   - Copy the contents from `.tasks/advancements/10_early_staging_deployment/nginx.conf.example`.
   - *Note:* Since the frontend is on Firebase, you can remove the `/` location block serving static files from Nginx, or just point the root API to `/api`.
   - Link it: `sudo ln -s /etc/nginx/sites-available/masteroflaw.ge /etc/nginx/sites-enabled/`.
   - Remove the default config: `sudo rm /etc/nginx/sites-enabled/default`.
3. **Certbot (Let's Encrypt):**
   - Install Certbot: `sudo apt install certbot python3-certbot-nginx`.
   - Generate SSL certificate: `sudo certbot --nginx -d masteroflaw.ge -d www.masteroflaw.ge`.
   - Certbot will automatically update your Nginx config with the correct SSL certificate paths.
   - Restart Nginx: `sudo systemctl restart nginx`.

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
