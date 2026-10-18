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
///
/// ---
///
/// 🔴 **This widget assumes NOTHING about the app, and that is the whole point
/// (`T-0260`, M18).** It is `ErrorWidget.builder` in release: it is built
/// *because* something else already threw, so every invariant the rest of the
/// app may take for granted is exactly what it must not require.
///
/// The M12 version required three of them, each of which can be absent
/// precisely when this screen is needed:
///
/// 1. **A kit `Theme`.** `context.fuzzzyColors` is
///    `Theme.of(context).extension<FuzzzyColors>()!`. If the throw happened at
///    or above `MaterialApp` — and `FuzzzyLawTheme.dark()` itself can
///    throw, since `_georgianize` does
///    `GoogleFonts.notoSansGeorgian(...).fontFamily!` over an HTTP fetch
///    (`T-0252`) — then no `Theme` carrying `FuzzzyColors` exists, the `!`
///    throws, and **the error widget throws from inside error handling.** The
///    user gets a blank screen instead of a message.
/// 2. **`MediaQuery`.** `Scaffold` and `SafeArea` both call `MediaQuery.of`,
///    which *asserts* rather than returning null.
/// 3. **`Directionality`.** `Text` cannot lay out without one.
///
/// So: the roles fall back to the kit's own **static ink tokens**, which are
/// plain `const` values needing no `Theme` at all — the design system is still
/// the source of every colour and size here, only its *delivery* failed, and
/// falling back to hardcoded hexes would have been both a literal and a lie.
/// `Theme.of` itself is safe to call bare (it returns `_kFallbackTheme` and
/// tolerates missing `Localizations`), so it is used for the lookup and never
/// for a value. And when the ancestors `Scaffold` needs are missing, the tree
/// degrades to `Directionality` + `ColoredBox` + `Center`, which need nothing.
///
/// Honest framing: the hazard *class* is inherited — the fork's
/// `PrimaryErrorPageView` banged on `context.uiColors` the same way. But M12
/// rewrote this file from scratch, and a crash screen is the one surface that
/// must not assume the app's invariants hold. Locked by
/// `test/app_error_page_view_test.dart`, which pumps it into a **bare tree**
/// with no `MaterialApp`, no `Theme`, no `MediaQuery` and no `Directionality`
/// — and was seen to throw before this change.
class AppErrorPageView extends StatelessWidget {
  const AppErrorPageView({
    required this.message,
    super.key,
  });

  /// Human-readable fault text. Not a stack trace — this is release mode.
  final String message;

  @override
  Widget build(BuildContext context) {
    // `Theme.of` never throws and never returns null, even with no ancestor.
    // The EXTENSIONS can still be absent, which is the case that matters.
    final theme = Theme.of(context);
    final colors = theme.extension<FuzzzyColors>() ?? FuzzzyColors.inkNight;
    final type = theme.extension<FuzzzyTextStyles>() ?? FuzzzyTextStyles.inkNight;
    final space = theme.extension<FuzzzySpace>() ?? FuzzzySpace.inkNight;

    final Widget message0 = Padding(
      padding: EdgeInsets.symmetric(horizontal: space.l),
      child: Text(
        message,
        textAlign: TextAlign.center,
        style: type.body.copyWith(
          color: colors.destructiveText,
          // Explicit: with no `DefaultTextStyle` ancestor Flutter paints text
          // with debug-yellow double underlines, and a bare tree is exactly
          // the situation this widget now has to survive.
          decoration: TextDecoration.none,
        ),
      ),
    );

    // `Scaffold` and `SafeArea` assert on a missing `MediaQuery`; `Text`
    // asserts on a missing `Directionality`. Both are guaranteed under
    // `MaterialApp` and neither is guaranteed above it.
    final full =
        MediaQuery.maybeOf(context) != null &&
        Directionality.maybeOf(context) != null;

    return Semantics(
      identifier: 'page.app_error',
      container: true,
      child: KeyedSubtree(
        key: const Key('page.app_error'),
        child: full
            ? Scaffold(
                body: GestureDetector(
                  // Only wired on the full path: `FocusScope.of` asserts
                  // without a `Focus` ancestor, and a crash screen whose tap
                  // handler crashes is the same bug one level down.
                  onTap: () => FocusScope.of(context).unfocus(),
                  child: SafeArea(child: Center(child: message0)),
                ),
              )
            : Directionality(
                textDirection: TextDirection.ltr,
                child: ColoredBox(
                  color: colors.ground,
                  child: Center(child: message0),
                ),
              ),
      ),
    );
  }
}
