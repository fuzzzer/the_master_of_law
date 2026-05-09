# Task: Authentication and Credits

> **Covers:** Full User Auth, Credit System, Usage Tracking
> **Dependencies:** `10_early_staging_deployment`

---

## Purpose

After the initial staging and testing phase using temporary API keys, we need to implement the final, robust authentication and credit system for production. This will allow public user registration, secure session management, and monetization through a credit-based usage system for AI queries.

---

## Multi-Step Guide

### Milestone 1: User Authentication
1. Implement proper user signup and login (Firebase Auth, JWT, or similar).
2. Create database tables for User Profiles.
3. Replace the temporary API key middleware with standard authentication middleware.
4. **Verify:** Users can register, log in, and securely access their own data.

### Milestone 2: Credit System Backend
1. Design a `Credits` table/model linked to the User.
2. Implement logic to deduct credits upon AI generation.
3. Prevent generation if the user has insufficient credits.
4. **Verify:** AI generation correctly reduces user credit balance, and blocks if balance is 0.

### Milestone 3: Credit System Frontend
1. Display the current credit balance in the UI.
2. Show warnings when credits are low or depleted.
3. Handle "Insufficient Credits" errors gracefully in the chat.
4. **Verify:** The user is always aware of their credit balance.

### Milestone 4: Migration & Clean up
1. Remove the temporary API key logic from `10_early_staging_deployment`.
2. Clean up any leftover temporary keys.
3. **Verify:** The temporary API key system is fully decommissioned and the app relies completely on the new auth system.
