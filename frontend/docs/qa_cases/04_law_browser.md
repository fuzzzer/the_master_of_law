# QA Test Case: Law Browser & Search

**Feature:** Static browsing and full-text searching of the 12 legal codes in the system.
**Goal:** Verify navigation hierarchy, search speed, and article reading UX.

## TC-01: Category Navigation
**Pre-conditions:** Logged in, on the "Laws" tab.
1. Observe the top-level list of legal categories (Civil, Criminal, Administrative, etc.).
   - **Expected:** Icons/colors are consistent.
2. Tap "Civil Law".
   - **Expected:** Navigates to a list of sub-codes (e.g., Civil Code, Civil Procedure Code).
3. Tap "Civil Code".
   - **Expected:** Displays the hierarchical structure of the code (Books → Titles → Chapters → Articles).
4. Tap an Article.
   - **Expected:** Navigates to the Article Reader view.

## TC-02: Article Reader UX
**Pre-conditions:** User is viewing a specific Article (e.g., Article 170).
1. Read the text.
   - **Expected:** Typography must be Noto Sans Georgian. Font size must be comfortable for reading. Line height should be spacious.
2. Pinch-to-zoom or use font-size controls (if implemented).
   - **Expected:** Text scales without breaking layout.
3. Tap "Explain this in plain language".
   - **Expected:** An AI bottom sheet appears summarizing the dense legal text into understandable concepts.

## TC-03: Full-Text Search Performance
**Pre-conditions:** On the "Laws" tab search bar.
1. Type a keyword: "მემკვიდრეობა" (Inheritance).
2. Tap Search / Enter.
   - **Expected:** Loading indicator briefly appears. Results list populates with relevant articles.
3. Observe results.
   - **Expected:** The keyword is highlighted/bolded in the result snippets.
4. Tap a result.
   - **Expected:** Routes to the exact Article, maintaining the search highlight if possible.

## TC-04: Offline Fallback (If supported)
**Pre-conditions:** Disconnect network.
1. Browse a previously visited legal code.
   - **Expected:** Cached articles load instantly.
2. Attempt a full-text search.
   - **Expected:** Fails gracefully indicating search requires network access.
