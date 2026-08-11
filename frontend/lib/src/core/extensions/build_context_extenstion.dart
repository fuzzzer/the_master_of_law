import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

/// App-level `BuildContext` conveniences.
///
/// **Phase M · M10.** The three fork role getters that used to live here —
/// `uiColors`, `uiTextStyles`, `uiFormStyles` — were deleted at this
/// checkpoint, together with the `package:ui_kit` import that typed them.
/// Deleting them is the migration's completeness check: after M2–M9b swapped
/// 963 role reads across 32 files, `analyze` had to name every site that still
/// wanted the fork, and it named **none**.
///
/// Design roles now come from the kit's own extensions and are read at the
/// point of use, never threaded through constructors:
///
/// ```dart
/// final colors  = context.fuzzzyColors;
/// final type    = context.fuzzzyTextStyles;
/// final space   = context.fuzzzySpace;
/// final radius  = context.fuzzzyRadius;
/// final density = context.fuzzzyDensity;
/// final motion  = context.fuzzzyMotion;
/// final form    = context.fuzzzyFormStyles;
/// ```
///
/// Hoist them into a local when a widget reads one several times — each getter
/// is a `Theme.of(this)` lookup. Do **not** hoist one you then do not use: it
/// becomes an `unused_local_variable` WARNING, which is a gate failure, not a
/// hint (JOURNAL M9 judgement 9).
extension BuildContextExtension on BuildContext {
  ThemasteroflawLocalizations get themasteroflawLocalizations =>
      ThemasteroflawLocalizations.of(this)!;
}
