import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · **M18 — the `T-0260` lock.**
///
/// [AppErrorPageView] is installed as `ErrorWidget.builder` under
/// `kReleaseMode` (`initializer.dart:32-38`). It is built **because something
/// else already threw**, so every invariant the rest of the app takes for
/// granted is precisely what it must not require.
///
/// The M12 version required three, and each is absent exactly when this screen
/// is needed — a throw at or above `MaterialApp`:
///
/// | required | how it failed |
/// |---|---|
/// | a kit `Theme` | `context.fuzzzyColors` is `…extension<FuzzzyColors>()!` → the `!` throws |
/// | `MediaQuery` | `Scaffold` / `SafeArea` call `MediaQuery.of`, which **asserts** |
/// | `Directionality` | `Text` cannot lay out without one |
///
/// The result was an error widget that throws from inside error handling: a
/// blank screen instead of a message, on the one surface with no second chance.
///
/// 🔴 **Why this file is the only possible evidence.** `ErrorWidget.builder` is
/// only installed in release, and a debug run paints Flutter's own red error
/// screen instead — so this widget is *structurally unreachable* by the M14
/// device matrix (HANDOFF §3.6), and no amount of Marionette driving will ever
/// exercise it. S9's live verifier reached everything else it was told it could
/// not; it could not reach this. A widget test in a deliberately bare tree is
/// the substitute, and it is a good one, because the bare tree is a *closer*
/// model of "MaterialApp never built" than any running app is.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  GoogleFonts.config.allowRuntimeFetching = false;

  const message = 'Unexpected App Crash';

  group('the catastrophic path — NOTHING is provided', () {
    testWidgets('renders in a tree with no MaterialApp, Theme, MediaQuery or '
        'Directionality', (tester) async {
      // `pumpWidget` supplies only a `View`. There is no `MaterialApp`, no
      // `Theme`, no `MediaQuery`, no `Directionality`, no `Focus` scope — the
      // shape of the tree when `ThemasteroflawTheme.dark()` itself throws and
      // `MaterialApp` never builds. Before M18 this threw a null-check error
      // on `extension<FuzzzyColors>()!`; SEEN RED.
      await tester.pumpWidget(const AppErrorPageView(message: message));

      expect(
        tester.takeException(),
        isNull,
        reason: 'the crash screen must not crash',
      );
      expect(
        find.text(message),
        findsOneWidget,
        reason: 'the user must still be told what happened',
      );
    });

    testWidgets('falls back to the KIT ink tokens, never to a raw literal', (
      tester,
    ) async {
      await tester.pumpWidget(const AppErrorPageView(message: message));

      final style = tester.widget<Text>(find.text(message)).style!;
      expect(
        style.color,
        FuzzzyColors.inkNight.destructiveText,
        reason:
            'the design system is still the source — only its Theme delivery '
            "failed, so the fallback is the kit's own static token set. "
            'Hardcoded hexes here would be both a literal and a lie.',
      );
      expect(style.fontSize, FuzzzyTextStyles.inkNight.body.fontSize);
      expect(
        style.decoration,
        TextDecoration.none,
        reason:
            'with no DefaultTextStyle ancestor Flutter paints debug-yellow '
            'double underlines, and a bare tree is exactly this case',
      );

      // The degraded tree must not reach for anything that asserts.
      expect(find.byType(Scaffold), findsNothing);
      expect(find.byType(SafeArea), findsNothing);
      expect(find.byType(ColoredBox), findsOneWidget);
    });

    testWidgets('still carries its QA identifier when degraded', (
      tester,
    ) async {
      await tester.pumpWidget(const AppErrorPageView(message: message));
      // M14 needs to be able to assert this screen did *not* appear; an
      // identifier that only exists on the healthy path cannot support that.
      expect(find.byKey(const Key('page.app_error')), findsOneWidget);
      expect(
        tester.getSemantics(find.byKey(const Key('page.app_error'))).identifier,
        'page.app_error',
      );
    });
  });

  group('the healthy path is unchanged', () {
    Future<void> pumpThemed(WidgetTester tester) async {
      late ThemeData theme;
      runZonedGuarded(() => theme = ThemasteroflawTheme.dark(), (e, _) {});
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const AppErrorPageView(message: message),
        ),
      );
    }

    testWidgets('uses the real Scaffold and the THEME roles, not the '
        'fallbacks', (tester) async {
      await pumpThemed(tester);
      expect(tester.takeException(), isNull);
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byType(SafeArea), findsOneWidget);

      final ctx = tester.element(find.text(message));
      final style = tester.widget<Text>(find.text(message)).style!;
      expect(style.color, ctx.fuzzzyColors.destructiveText);
      expect(
        style.fontFamilyFallback,
        isNotEmpty,
        reason:
            'the themed path must still pick up the app-side Georgian '
            'fallback — the static token set has none, so a silent switch to '
            'the degraded path would show up here',
      );
    });

    testWidgets('a long Georgian message stays inside the gutter and does not '
        'overflow', (tester) async {
      // The one deliberate improvement over the fork, kept under test: its
      // bare `Center(child: Text(...))` let a long message run edge to edge.
      final errors = <String>[];
      final previous = FlutterError.onError;
      FlutterError.onError = (d) {
        errors.add('${d.exception}');
        previous?.call(d);
      };
      addTearDown(() => FlutterError.onError = previous);

      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(360, 800);
      addTearDown(tester.view.reset);

      late ThemeData theme;
      runZonedGuarded(() => theme = ThemasteroflawTheme.dark(), (e, _) {});
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const MediaQuery(
            data: MediaQueryData(
              size: Size(360, 800),
              textScaler: TextScaler.linear(1.3),
            ),
            child: AppErrorPageView(
              message: 'აპლიკაციაში მოხდა მოულოდნელი შეცდომა, '
                  'გთხოვთ სცადოთ თავიდან',
            ),
          ),
        ),
      );
      tester.takeException();
      expect(errors, isEmpty, reason: errors.join('\n'));
    });
  });
}
