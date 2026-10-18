# Flutter Architecture & Standards Guide

> This is the canonical, production-grade architecture and standards document. All AI personas MUST adhere to these rules without exception. This is the single source of truth for "how we build things."

---

## 1. High-Level System Design

### Visual Map — System Architecture
```mermaid
graph TB
    subgraph EntryPoints["Entry Points"]
        MD[main_development.dart]
        MS[main_staging.dart]
        MP[main_production.dart]
    end

    subgraph AppShell["App Shell — lib/src/app/"]
        ENV[Environment Config]
        INIT[Initializer]
        APP[FuzzyApp]
        NAV[AppRouter / GoRouter]
        GBP[GlobalBlocProviders]
        THEME_CUBIT[ThemeCubit]
        L10N_CUBIT[LocalizationCubit]
        BLOC_OBS[AppBlocObserver]
    end

    subgraph CoreLayer["Core Layer — lib/src/core/"]
        DI[DependencyInjection]
        SL[ServiceLocator / GetIt]

        subgraph HTTP["HTTP Client Stack"]
            HCI[HttpClientInterface]
            FHC[FuzzyHttpClient]
            FPHC[FuzzyPublicHttpClient]
            API_INT[ApiInterceptor]
            AUTH_INT[AuthInterceptor]
            LOG_INT[LoggingInterceptor]
            NET_CFG[ApiNetworkConfiguration]
            EXC_TRANS[RestApiExceptionTranslator]
        end

        subgraph Exceptions["Exception Hierarchy"]
            HCE[HttpClientException]
            DE[DeserializationException]
            NE[NetworkException]
            URE[UnsuccessfulResponseException]
            CEE[ClientErrorException — 4xx]
            SEE[ServerErrorException — 5xx]
        end

        subgraph StateEnums["BLoC State Enums"]
            SS[StateStatus]
            ASS[ActionStateStatus]
            FSS[FilterStateStatus]
            OUS[OptimisticUpdateStatus]
            AT[ActionType]
        end

        subgraph Services["Services"]
            CACHE[ApiCacheService / Hive]
            SEC[SecureStorageService]
            LOGGER[AppLogger / LogManager]
            DEVPANEL[DevPanelService]
            DUH[DataUpdatesHub]
        end
    end

    subgraph Features["Feature Modules — lib/src/feature_name/"]
        subgraph PaymentsFeature["payments/ — Reference Implementation"]
            PM[models/]
            PDS[data/data_sources/]
            PR[data/repositories/]
            PB[bloc/]
        end
        FUTURE_FEAT["Future features follow same structure"]
    end

    subgraph UIKit["packages/ui_kit/"]
        THEME[UiKitTheme — light/dark]
        COLORS[UiKitColors]
        TXT[UiKitTextStyles]
        FORMS[UiFormStyles]
        WIDGETS[Widgets — PrimaryButton, etc]
        ICONS[UiKitIcon / SVG]
    end

    subgraph CodeGen["code_generators/bricks/"]
        B1[remote_feature_template_brick]
        B2[paginated_remote_feature_template_brick]
        B3[form_page_brick]
    end

    %% Flow
    MD & MS & MP --> ENV
    ENV --> INIT
    INIT --> DI
    DI --> SL
    INIT --> APP
    APP --> GBP
    APP --> NAV
    PDS --> FHC
    PR --> PDS
    PB --> PR
    B1 & B2 & B3 -.->|generates| Features
```

### Data Flow — Feature Request Lifecycle
```mermaid
sequenceDiagram
    participant UI as UI Widget
    participant Cubit as FeatureCubit
    participant Repo as FeatureRepository
    participant DS as FeatureDataSource
    participant HTTP as FuzzyHttpClient
    participant API as Remote API

    UI->>Cubit: call method(requestParams)
    Cubit->>Cubit: emit(state.copyWith(status: loading))
    Cubit->>Repo: repoMethod(requestParams)
    Repo->>DS: dataSourceMethod(requestParams)
    DS->>HTTP: post(uri, body)
    HTTP->>API: Dio request with interceptors
    API-->>HTTP: Response
    HTTP-->>DS: Response of T or throws HttpClientException
    DS-->>Repo: ModelData
    Repo-->>Cubit: sealed Response — Success or Failure
    Cubit->>Cubit: switch on response type
    alt Success
        Cubit->>Cubit: emit(state.copyWith(status: success, data: ...))
    else Failure
        Cubit->>Cubit: emit(state.copyWith(status: failed, failureType: ...))
    end
    Cubit-->>UI: BlocBuilder rebuilds
```

---

## 2. Directory Structure & Module Responsibilities

This is the canonical directory map. The AI must create files and features that fit perfectly within this structure.

```
frontend/
├── lib/
│   ├── main_development.dart
│   ├── main_staging.dart
│   ├── main_production.dart
│   └── src/
│       ├── src.dart                  # Root barrel
│       ├── app/                      # App Shell: Routing, Theme, Globals, Init
│       ├── core/                     # Core Layer: DI, HTTP, Exceptions, Services
│       └── features/                 # Feature Modules (e.g., payments/)
├── packages/
│   └── ui_kit/                     # Design System Package
├── code_generators/bricks/         # Mason Code Generation Templates
└── ...
```

---

## 3. Feature Folder Structure (Canonical Pattern)

Every feature module MUST follow this structure. This is non-negotiable.

### 3.1. Layers within a Feature (`lib/src/<feature_name>/`)
-   **`models/`**: Plain Dart data classes with `toMap`/`fromMap`. Naming: `<Name>Data` for responses, `<Name>RequestParameters` for requests.
-   **`data/`**:
    -   `data_sources/`: Handles raw data fetching (HTTP calls). Accesses `sl.get<FuzzyHttpClient>()`.
    -   `repositories/`: Facade over data sources. **MUST** catch all exceptions and return a Sealed Class response. Takes data source via constructor injection.
-   **`bloc/`**: Cubits/Blocs and their immutable State classes. Takes repository via constructor injection. State file uses `part of`.
-   **`view/`**: `pages/` (route destinations) and `components/` (feature-specific widgets).

### 3.2. Barrel Files & `./exp.sh` (MANDATORY)
Every directory MUST have a barrel file (`<dir_name>.dart`) that exports its children. After creating any new `.dart` files, the user **MUST** be reminded to run `./exp.sh` to automatically update this entire barrel chain. Failure to do so will result in compilation errors.

**Opting a file out — `// exporter:ignore` (added Phase M · M13).** A file whose
first lines contain `// exporter:ignore` on a line of its own is never exported
from its folder barrel, and any existing export of it is removed. This exists
for the **two halves of a conditional import** (`dependency_injection_native/web`
and `shake_native/web`): both halves declare the same top-level names by design,
so exporting both is `ambiguous_export` and the app stops compiling.

Before M13, `scripts/exporter.py` had no opt-out and *unioned* its computed
exports with whatever the barrel already contained — so deleting the offending
line by hand could never stick, and `./exp.sh` had to be followed by a
`git checkout --` of three barrels every single time. **`./exp.sh` is now safe
to run blind, and is idempotent.** Put the marker in the excluded file next to
the reason; never hand-trim a generated barrel.

---

## 4. Architectural Patterns & Rules

### 4.1. BLoC/Cubit & Repository Contract
-   **Repositories NEVER throw exceptions.** They return Sealed Classes (`Success | Failure`). This is the most important rule.
-   **Cubits NEVER use `try/catch`.** They use exhaustive `switch` on the sealed response.
-   **State MUST be immutable.** Use `copyWith`.
-   State status is tracked via `StateStatus` enum (`initial`, `loading`, `success`, `failed`).

### 4.2. Dependency Injection (GetIt)
-   **Constructor Injection is MANDATORY** for Repositories and Cubits.
-   **Service Locator (`sl.get<T>()`) is ONLY permitted** in the `data_sources/` layer (for `HttpClient`) and at the top level when providing a BLoC. It is forbidden in Widgets, Repositories, and Cubits.

### 4.3. UI Kit & Theming

> **Updated Phase M · M12 (2026-08-11).** The forked `packages/ui_kit` **no longer
> exists**. The app consumes the shared design system `fuzzzy_ui_kit`
> (`path: ../../fuzzy_design`) through its single barrel
> `package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart`. `fuzzy_design` is **read-only** to app
> agents: never fork it, never edit it. Its consumer law is `design/USING.md`, and
> `fvm dart run fuzzzy_ui_kit:guard lib --allow=.fuzzzy_guard_allow` enforces it.

-   **NEVER** use `Color()`, `Colors.`, `TextStyle()`, or hardcoded numbers for spacing/padding/radii/durations. Every one of them is a **role**.
-   **ALWAYS** read roles from the `BuildContext` at the point of use: `context.fuzzzyColors`, `context.fuzzzyTextStyles`, `context.fuzzzySpace`, `context.fuzzzyRadius`, `context.fuzzzyDensity`, `context.fuzzzyMotion`, `context.fuzzzyFormStyles`. The old `context.uiColors` / `uiTextStyles` / `uiFormStyles` getters were deleted at M10 and do not exist.
-   **ALWAYS** prefer a `Fuzzzy*` widget from the kit (`FuzzzyButton`, `FuzzzyCard`, `FuzzzyTextField`, `FuzzzyToast`, …) over a native Flutter widget. `PrimaryScaffold` / `PrimaryButton` / `PrimaryTextField` and the rest of the fork's widgets are **gone**.
-   If no kit widget fits, **build it app-side on roles** (`design/RECIPE_NEW_WIDGET.md`) — see `lib/src/features/cases/view/components/app_status_chip.dart` for the worked example. Never add a literal, never fork the kit.
-   `lib/src/app/theme/fuzzzy_law_theme.dart` is the **one** bridge from kit roles to `ThemeData`, including the Georgian `fontFamilyFallback` every type role carries (the Ink pack's families have no Georgian block).

### 4.4. Error Handling Protocol
1.  **HTTP Client Level:** The `FuzzyHttpClient` and its `RestApiExceptionTranslator` automatically convert `DioException`s into a rich hierarchy of typed `HttpClientException`s.
2.  **Data Source Level:** Data sources make HTTP calls. They may let these typed exceptions bubble up.
3.  **Repository Level:** The repository wraps the data source call in a `try/catch` block. It catches ALL exceptions and translates them into a `Failure` object within its sealed response.
4.  **Cubit Level:** The cubit receives the `Failure` object and maps it to a `StateStatus.failed` state, passing along a specific `FailureType` enum.
5.  **UI Level:** The UI uses a `StatusBuilder` widget to react to `StateStatus.failed` and displays an appropriate error message based on the `FailureType`.

---

## 5. Code Generation & Scripts

The AI should prefer using scripts over manual creation.

-   **`./gen.sh <brick_name>`**: Use Mason to scaffold entire features (`remote_feature_template_brick`), pages (`form_page_brick`), etc.
-   **`./exp.sh`**: Mandatory after creating any new file.
-   **`./loc.sh "Text||lang||Translation"`**: Add localizations. No hardcoded user-facing strings.
-   ~~`./add_icon.sh path/to/icon.svg icon_name`~~: **Removed.** It wrote into the forked `packages/ui_kit`, which was deleted at M12, and the script itself is not present in this repo. Icons now come from the kit or from Material's own icon set.

---

## 6. Linter & Formatting
The project uses `very_good_analysis` with some disabled rules for practicality (e.g., 80 char line limit). The [REVIEWER] persona must run `fvm flutter analyze` and `fvm dart format --set-exit-if-changed .` as part of its process.
