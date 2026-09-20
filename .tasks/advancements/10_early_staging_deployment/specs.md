# Specs: Early Staging Deployment

## Behavioral Specs

| Scenario | System State | User Interface Should Show |
| :--- | :--- | :--- |
| User opens app without key | Key missing | Prompt to enter Access Key |
| User enters valid key | Key valid | Main application (Chat, etc.) |
| User enters invalid key | Key invalid | Error message "Invalid Access Key" |
| Admin requests new key | Valid Admin Key | Returns new generated User API Key |

## Technical Constraints

- **Hosting:** Hetzner VPS.
- **DNS/CDN:** Cloudflare.
- **Web Server:** Nginx (Reverse proxy for FastAPI backend on port 8000 and Flutter Web/App on 80/443).
- **Auth Data Store:** Can use Redis, a simple SQLite file, or the existing PostgreSQL DB to store the valid User API keys.
- **Key Header:** `X-API-Key: <key>` for backend requests.

## Go/No-Go Criteria

- [ ] The app is accessible via the public domain.
- [ ] No unauthorized access to any backend routes (except health checks).
- [ ] Nginx is properly routing traffic.
