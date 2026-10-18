# Progress: Staged Deployment Plan

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Production Infrastructure Audit
- [ ] Read `.agents/context/production.md`
- [ ] Verify VPS and backend health
- [ ] Verify SSL/TLS configuration
- [ ] Verify domain DNS records
- [ ] Health check passes from external
- [ ] **Milestone complete:** Infrastructure verified ✅

## Milestone 2: Web Build & Deploy Pipeline
- [ ] Configure Flutter web build for production
- [ ] Set up Nginx for web hosting
- [ ] Configure API proxy in Nginx
- [ ] Configure WebSocket proxy
- [ ] Enable gzip and caching
- [ ] HTTPS via Let's Encrypt
- [ ] Create `scripts/deploy-web.sh`
- [ ] **Milestone complete:** Web deployed and accessible ✅

## Milestone 3: Pre-Launch Checklist (Web)
- [ ] Security checklist passed
- [ ] Performance checklist passed
- [ ] Content checklist passed (localization, error messages)
- [ ] Privacy policy page live
- [ ] Terms of service page live
- [ ] Monitoring configured
- [ ] **Milestone complete:** All checklist items green ✅

## Milestone 4: Web Launch & Smoke Test
- [ ] Deploy to production
- [ ] Register new user test
- [ ] Chat message test
- [ ] Law browsing test
- [ ] Case creation test
- [ ] Credits test
- [ ] Monitor logs for 24 hours
- [ ] Collect initial feedback
- [ ] **Milestone complete:** Web live and stable for 24h ✅

## Milestone 5: Mobile Build Configuration
- [ ] Android build configuration
- [ ] Android signing keys
- [ ] Android build succeeds
- [ ] iOS build configuration
- [ ] iOS signing certificates
- [ ] iOS build succeeds
- [ ] **Milestone complete:** Both platforms build clean ✅

## Milestone 6: App Store Preparation
- [ ] Google Play developer account
- [ ] Google Play store listing
- [ ] Google Play internal testing upload
- [ ] Google Play internal testing verified
- [ ] App Store Connect entry
- [ ] App Store metadata
- [ ] TestFlight upload
- [ ] TestFlight testing verified
- [ ] **Milestone complete:** Both stores accept builds ✅

## Milestone 7: Mobile Launch
- [ ] Google Play production release
- [ ] iOS App Review submitted
- [ ] iOS approved and released
- [ ] Firebase Crashlytics monitoring
- [ ] First 10 installs successful
- [ ] **Milestone complete:** Available on both stores ✅

---

## Blockers / Notes

_None yet._
