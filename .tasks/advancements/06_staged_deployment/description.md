# Task: Staged Deployment Plan

> **Covers:** Task 9 (Staged Deployment Plan)
> **Dependencies:** Ideally Task 04 (QA) and Task 05 (Docs) are complete before production release.

---

## Purpose

Execute a staged release plan for The Master of Law. Deploy in phases to minimize risk:
1. **Phase 1: Web** — Deploy Flutter web to a public URL. Fastest to ship, easiest to iterate.
2. **Phase 2: Mobile** — Release Android (Google Play) and iOS (App Store) after web is validated.

Each phase has its own checklist, infrastructure requirements, and go/no-go criteria.

---

## Multi-Step Guide

### Milestone 1: Production Infrastructure Audit
1. Read `.agents/context/production.md` for existing production setup
2. Verify VPS configuration:
   - Backend is running and accessible
   - PostgreSQL, ChromaDB, Redis are healthy
   - SSL/TLS configured for API domain
   - CORS configured for web domain
3. Verify domain setup:
   - API domain: `api.masteroflaw.ge` (or equivalent)
   - Web domain: `masteroflaw.ge` (or equivalent)
   - DNS records pointing to VPS
4. **Verify:** `curl https://api.domain/api/v1/health` returns 200

### Milestone 2: Web Build & Deploy Pipeline
1. Configure Flutter web build:
   - `cd fuzzy_starter && flutter build web --release`
   - Configure API base URL for production
   - Configure Firebase auth for production (web client)
2. Set up web hosting:
   - **Option A:** Serve from the same VPS via Nginx
   - **Option B:** Deploy to Firebase Hosting or Cloudflare Pages
   - **Recommendation:** Option A (same VPS, simpler, all in one place)
3. Write Nginx config for web:
   - Serve Flutter web static files
   - Proxy `/api/*` to backend on port 8000
   - Enable gzip compression
   - Configure caching for static assets
   - HTTPS via Let's Encrypt
4. Create deployment script `scripts/deploy-web.sh`:
   ```bash
   flutter build web --release
   rsync -avz build/web/ deploy@vps:/opt/master-of-law/web/
   ssh deploy@vps "sudo systemctl reload nginx"
   ```
5. **Verify:** Website loads at `https://masteroflaw.ge`, API calls work, chat produces a response

### Milestone 3: Pre-Launch Checklist (Web)
1. Security:
   - [ ] No API keys in client-side code
   - [ ] Firebase auth configured for production
   - [ ] CORS restricted to production domain only
   - [ ] Rate limiting active
   - [ ] Credit system active (not dev bypass)
2. Performance:
   - [ ] Web build is minified and tree-shaken
   - [ ] Assets gzipped
   - [ ] First Contentful Paint < 3s
   - [ ] Chat response time < 10s (including RAG + Gemini)
3. Content:
   - [ ] Georgian localization complete
   - [ ] Error messages user-friendly (not raw HTTP)
   - [ ] Privacy policy page (required for app stores later)
   - [ ] Terms of service page
4. Monitoring:
   - [ ] Backend logs accessible (`docker compose logs`)
   - [ ] Health check endpoint monitored
   - [ ] Error alerting (simple: cron + curl health check → email)
5. **Verify:** All checklist items pass

### Milestone 4: Web Launch & Smoke Test
1. Deploy to production
2. Run full smoke test:
   - Register new user
   - Send a chat message, receive AI response
   - Browse laws
   - Create a case file
   - Check credits
3. Monitor logs for 24 hours
4. Collect initial user feedback
5. **Verify:** No errors in logs for 24 hours, feedback collected

### Milestone 5: Mobile Build Configuration
1. Android:
   - Verify `android/app/build.gradle` has correct `applicationId`: `ge.fuzzycore.masteroflaw`
   - Configure signing keys (keystore)
   - Build: `flutter build appbundle --release`
   - Test on physical device via `flutter install`
2. iOS:
   - Verify `ios/Runner.xcodeproj` has correct bundle ID: `ge.fuzzycore.masteroflaw`
   - Configure signing certificates and provisioning profiles
   - Build: `flutter build ios --release`
   - Test on physical device via Xcode
3. **Verify:** Both APK/AAB and IPA build without errors

### Milestone 6: App Store Preparation
1. Google Play:
   - Create developer account (if not exists)
   - Prepare store listing: title, description (Georgian + English), screenshots, icon
   - Privacy policy URL
   - Content rating questionnaire
   - Upload AAB to internal testing track
   - Test via Google Play internal testing
2. Apple App Store:
   - Create App Store Connect entry
   - Prepare metadata: description, screenshots, keywords
   - Privacy policy URL
   - App Review guidelines compliance check
   - Upload to TestFlight
   - Test via TestFlight
3. **Verify:** Both stores accept the build, internal testers can install

### Milestone 7: Mobile Launch
1. Promote Google Play from internal → open testing → production
2. Submit iOS for App Review
3. Coordinate release timing: both platforms within same week
4. Monitor crash reports (Firebase Crashlytics)
5. **Verify:** App available on both stores, first 10 installs successful
