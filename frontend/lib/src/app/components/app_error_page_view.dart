import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// The release-mode crash screen — what `ErrorWidget.builder` paints when a
/// widget throws during build (`Initializer.preAppInit`).
///
/// Phase M · Unit A · M12. Replaces the fork's `PrimaryErrorPageView`, which
/// died with `packages/ui_kit`. Built app-side on kit roles per
/// `RECIPE_NEW_WIDGET.md`; there is no kit widget for this — `FuzzzyEmptyState`
/// is a *panel* for an empty list, not a full-screen fault, and it carries the
/// brand sun-disc, which is the wrong voice for a crash.
///
/// **Nothing was lost with the fork's version.** It rendered
/// `PrimaryScaffold(hasAutomaticBackButton: true, body: Center(Text(message)))`
/// with the message in `body16`/`errorColor`. `hasAutomaticBackButton` on
/// `PrimaryScaffold` only ever gated an `actionsRow`, and this call site passed
/// none — so it drew **no back button** and dropping the flag removes no
/// affordance. `PrimaryScaffold`'s tap-to-unfocus and `SafeArea` are kept.
///
/// Roles consumed: `ground` (inherited — `FuzzzyTheme.build` binds
///   `scaffoldBackgroundColor`) · `type.body` in `destructiveText` (MAPPING
///   §2.6: `errorColor` on destructive text → `destructiveText`) ·
///   `space.l` gutter.
/// States: rest only — non-interactive.
/// QA: `text.<qaId>`-free by design; carries the fixed `page.app_error`
///   identifier + `Key`, because a crash screen has exactly one instance and
///   M14 needs to be able to assert it did *not* appear.
///
/// One deliberate improvement over the fork: the message is padded off the
/// screen edges and centre-aligned. The fork's bare `Center(child: Text(...))`
/// let a long Georgian message run edge-to-edge at `textScaler` 1.3.
class AppErrorPageView extends StatelessWidget {
  const AppErrorPageView({
    required this.message,
    super.key,
  });

  /// Human-readable fault text. Not a stack trace — this is release mode.
  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final space = context.fuzzzySpace;

    return Semantics(
      identifier: 'page.app_error',
      container: true,
      child: Scaffold(
        key: const Key('page.app_error'),
        body: GestureDetector(
          onTap: () => FocusScope.of(context).unfocus(),
          child: SafeArea(
            child: Center(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: space.l),
                child: Text(
                  message,
                  textAlign: TextAlign.center,
                  style: context.fuzzzyTextStyles.body.copyWith(
                    color: colors.destructiveText,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
