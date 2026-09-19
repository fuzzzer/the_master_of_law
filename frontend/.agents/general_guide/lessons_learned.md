# LESSONS.md — Long-Term AI Memory

> This document contains hard-won knowledge from past bugs and architectural decisions. The [DOER] and [REVIEWER] personas MUST consult this file before any action to avoid repeating historical mistakes.

---

## Resolved Anti-Patterns

### AP-001: Never Throw from Repositories
**Problem:** Repositories throwing exceptions force cubits to use try/catch, leading to inconsistent error handling and forgotten catch blocks.
**Resolution:** Repositories return sealed class responses (`Success | Failure`). Cubits use exhaustive `switch`. No try/catch in BLoC layer.
**Rule:** If you write try/catch in a Cubit, you are violating the architecture.

### AP-002: Never Use Service Locator in Repositories or Cubits
**Problem:** Accessing dependencies via `sl.get<T>()` everywhere hides dependencies and makes testing impossible.
**Resolution:** Only data sources may access `sl` directly (for HTTP clients). Repositories receive data sources via constructor injection. Cubits receive repositories via constructor injection.
**Rule:** Constructor injection for repos and cubits. Service locator only at data source boundary.

### AP-003: Never Import Feature Files Directly
**Problem:** Importing `package:fuzzzy_law/src/payments/models/payment_method_data.dart` creates tight coupling.
**Resolution:** Always import through root barrel: `import 'package:fuzzzy_law/src/src.dart';`
**Rule:** One import. `import 'package:fuzzzy_law/src/src.dart';` is the only project import you write.

### AP-004: Never Skip Barrel Files
**Problem:** Missing barrel exports cause "undefined" errors.
**Resolution:** Every directory has a barrel file. Every new `.dart` file gets exported in its parent barrel immediately.
**Rule:** After file creation, the user must be prompted to run `./exp.sh`.

### AP-005: Never Hardcode Colors, Text Styles, or Spacing
**Problem:** Hardcoded values make theme changes impossible and lead to inconsistency.
**Resolution:** Use theme extensions: `context.uiColors`, `context.uiTextStyles`, `context.uiFormStyles`.
**Rule:** If you type `Color(`, `TextStyle(`, or a magic number for padding, you are violating the architecture.

---

## Historical Bugs & Fixes

### BUG-001: Safe Registration Required for GetIt
**Context:** Standard `GetIt.registerSingleton<T>()` throws if already registered (common during hot restarts or in test setups).
**Fix:** Use the custom `safeRegisterSingleton` / `safeRegisterLazySingleton` extensions that internally check `sl.isRegistered<T>()`.
**Lesson:** Always use the `safe*` registration variants provided in the project.

### BUG-002: Dio connectTimeout vs receiveTimeout
**Context:** Setting only one timeout leaves the other at Dio's default (which can be infinite), leading to requests that hang indefinitely.
**Fix:** The `DefaultBaseOptions` in the project sets both: `connectTimeout` (e.g., 20s) and `receiveTimeout` (e.g., 30s).
**Lesson:** Always ensure both timeouts are configured in any HTTP client setup.

---

## Framework Nuances & Best Practices

### FN-001: Dart 3 Sealed Classes for Repository Responses
**Nuance:** Sealed classes are the backbone of our error handling. They enable compile-time safety via exhaustive `switch` statements. Adding a new failure type will cause a compile error wherever it's not handled.
**Pro-Tip:** Embrace this. When adding a new failure case, add it to the sealed hierarchy and let the compiler guide you to all the places that need to be updated.

### FN-002: `part of` Directive for Cubit State
**Nuance:** State files use the `part of 'my_cubit.dart';` directive. This means the state file is lexically part of the cubit file; it can access the cubit's imports but cannot have its own `import` statements.
**Pro-Tip:** All necessary imports for the state must be placed in the main cubit file.

### FN-003: DataUpdatesHub for Cross-Feature Communication
**Nuance:** To avoid violating feature boundaries, features can communicate indirectly using the `DataUpdatesHub` service. One feature can broadcast an event (e.g., `userProfileUpdated`), and another feature's Cubit can listen to this stream to trigger a data refresh.
**Pro-Tip:** Use this for low-frequency, event-based communication. Do not use it for direct data passing.
