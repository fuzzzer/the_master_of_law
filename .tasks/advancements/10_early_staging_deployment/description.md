# Task: Early Staging Deployment

> **Covers:** Nginx, Hetzner VPS, Cloudflare, Temporary API Key Auth
> **Dependencies:** None

---

## Purpose

We need to host the application on a Hetzner VPS with a Cloudflare domain to allow custom users to test it before implementing full authentication and credit systems. To secure the app during this phase, we will implement a simple, temporary API key-based authentication system. An admin API key will be used to generate user API keys, which testers will use to access the site.

---

## Multi-Step Guide

### Milestone 1: Server Infrastructure Setup
1. Provision a Hetzner VPS.
2. Point the Cloudflare domain to the VPS IP.
3. Install and configure Nginx as a reverse proxy for the backend and frontend.
4. Set up SSL/TLS via Cloudflare or Let's Encrypt.
5. **Verify:** You can access the domain over HTTPS and see the application or backend health check.

### Milestone 2: Temporary API Key Auth (Backend)
1. Add an `ADMIN_API_KEY` to the backend environment variables.
2. Create an endpoint (protected by `ADMIN_API_KEY`) to generate and store user API keys.
3. Update existing endpoints to require a valid user API key via headers (e.g., `Authorization: Bearer <API_KEY>` or `X-API-Key`).
4. **Verify:** Requests without a valid API key are rejected with 401/403. Admin can successfully generate new keys.

### Milestone 3: Temporary API Key Auth (Frontend)
1. Add a simple UI prompt on the frontend requesting the API key before allowing access to the app.
2. Store the entered API key locally (secure storage).
3. Append the API key to all backend HTTP requests.
4. **Verify:** The app works normally once a valid API key is entered.

### Milestone 4: Deployment
1. Deploy the backend and frontend to the Hetzner VPS.
2. Provide test keys to the initial users.
3. **Verify:** External users can access and test the app using their assigned keys.
