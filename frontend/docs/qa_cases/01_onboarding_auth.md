# QA Test Case: Onboarding & Authentication

**Feature:** Initial app launch, onboarding screens, and user authentication (Firebase).
**Goal:** Ensure users can smoothly enter the app and understand its value proposition without friction.

## TC-01: First-time App Launch (Onboarding)
**Pre-conditions:** App installed freshly (or storage cleared). No active user session.
1. Launch the app.
2. Observe the Splash screen.
   - **Expected:** The splash screen loads quickly, respects the device's light/dark mode, and transitions smoothly to the first onboarding screen.
3. Swipe through the 3 onboarding screens.
   - **Expected:** Swiping is fluid. Each screen displays a relevant illustration and concise text. The pagination dots at the bottom update correctly.
4. On the final screen, click "Get Started".
   - **Expected:** Navigates to the Authentication (Login/Register) screen.

## TC-02: Anonymous Login (If applicable)
**Pre-conditions:** User is on the Auth screen.
1. Tap "Continue as Guest".
   - **Expected:** Instantly routes to the main Home/Chat tab. A temporary Firebase Auth session is created behind the scenes.
2. Go to Profile.
   - **Expected:** Shows guest status with a prompt to "Link Account" to save data.

## TC-03: Google Authentication
**Pre-conditions:** User is on the Auth screen.
1. Tap "Continue with Google".
2. Select a Google account from the native OS modal.
   - **Expected:** Loading indicator appears. Once authenticated, routes to the main Home/Chat tab.

## TC-04: Error Handling - Network Failure
**Pre-conditions:** Disconnect device from WiFi/cellular.
1. Attempt to login via Google.
   - **Expected:** A clear, non-technical error message appears (e.g., "No internet connection. Please check your network and try again.")
   - **Fail state:** App crashes or shows infinite loading spinner.
