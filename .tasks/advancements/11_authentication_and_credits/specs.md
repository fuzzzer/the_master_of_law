# Specs: Authentication and Credits

## Behavioral Specs

| Scenario | System State | User Interface Should Show |
| :--- | :--- | :--- |
| New user visits app | Unauthenticated | Login / Sign Up screen |
| User asks AI question | Sufficient credits | Question answered, balance updates |
| User asks AI question | Insufficient credits | "Not enough credits" error/prompt |

## Technical Constraints

- **Auth Provider:** Use Firebase Auth (as mentioned in existing architecture `RULE[GEMINI.md]`) or custom JWT if preferred.
- **Credit Tracking:** Requires atomic transactions in PostgreSQL to prevent race conditions when deducting credits.
- **Rate Limiting:** Must be integrated with the new auth system to prevent abuse.

## Go/No-Go Criteria

- [ ] Temporary API key system is completely removed.
- [ ] Users can securely authenticate.
- [ ] Credits are accurately deducted for each generation event.
- [ ] Users cannot bypass the credit check.
