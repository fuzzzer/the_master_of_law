# QA Test Case: Case Builder & Dashboard

**Feature:** The central hub where users manage their legal problems, categorize facts, view AI-generated arguments, and track evidence.
**Goal:** Verify complex data rendering, progressive disclosure UX, and case CRUD operations.

## TC-01: Create a New Case
**Pre-conditions:** Logged in, on the "Cases" tab.
1. Tap the Floating Action Button (FAB) or "New Case" button.
2. Enter a Case Title (e.g., "Property Boundary Dispute").
3. Select a Domain (e.g., "Civil").
4. Tap "Create Case".
   - **Expected:** The case is created instantly. You are navigated to the empty Case Dashboard.
   - **Visuals:** Empty states should show helpful illustrations and "Add your first fact" call-to-actions.

## TC-02: Adding Facts (Favorable/Unfavorable/Neutral)
**Pre-conditions:** On an empty Case Dashboard.
1. Tap "Add Fact" in the Facts section.
2. Enter "The neighbor built a fence 2 meters into my land."
3. Select type "Unfavorable".
4. Save.
   - **Expected:** Fact appears in the list. UI should use color coding (e.g., red tint for unfavorable) to distinguish it.
   - **Performance:** Adding a fact should feel instantaneous (optimistic UI update).

## TC-03: AI Argument Generation
**Pre-conditions:** A case exists with at least 3 facts.
1. Tap "Generate Legal Strategy" or "Analyze Facts".
2. Observe the loading state.
   - **Expected:** A skeleton loader or progress indicator shows while waiting for the backend.
3. Observe the generated Arguments.
   - **Expected:** AI returns numbered argument cards. Each card must have a "Strength" indicator (Strong/Moderate/Weak).
   - **Visuals:** Check for text overflow. Verify that markdown (bolding, lists) in the AI's response renders correctly in the Flutter UI.

## TC-04: Editing and Reordering Timeline
**Pre-conditions:** A case has multiple action items/timeline events.
1. Attempt to drag-and-drop to reorder action items.
   - **Expected:** Smooth drag physics. The new order persists.
2. Tap an action item to edit the deadline.
   - **Expected:** Native date-picker opens. Saving updates the item's position if sorted by date.

## TC-05: Scroll Performance on Large Cases
**Pre-conditions:** Mock a case with 50+ facts, 10 arguments, and 20 evidence items.
1. Scroll rapidly from top to bottom.
   - **Expected:** Consistently smooth 60fps scrolling. No jank or blank "building" widgets during rapid scroll.
