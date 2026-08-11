import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

class ThemasteroflawApp extends StatelessWidget {
  const ThemasteroflawApp({super.key});

  static Future<void> run() async {
    await Initializer.preAppInit();
    runApp(const ThemasteroflawApp());
    await Initializer.postAppInit();
  }

  @override
  Widget build(BuildContext context) {
    return GlobalBlocProviders(
      child: Builder(
        builder: (context) {
          return ThemeStateBuilder(
            builder: (themeBrightness) {
              return LocalizationStateBuilder(
                builder: (locale) {
                  return MaterialApp.router(
                    routerConfig: AppRouter.themasteroflawRouter,
                    // No `scaffoldMessengerKey:` — the app-wide
                    // `GlobalKey<ScaffoldMessengerState>` that used to live at
                    // the top of this file was deleted at M12. M11 replaced
                    // every `SnackBar` with `FuzzzyToast.show`, which resolves
                    // its own overlay from the call-site context, so the key
                    // had zero readers. `MaterialApp` creates its own
                    // `ScaffoldMessenger` when none is supplied.
                    theme: switch (themeBrightness) {
                      Brightness.dark => ThemasteroflawTheme.dark(),
                      Brightness.light => ThemasteroflawTheme.light(),
                    },
                    locale: Locale(locale.languageCode),
                    localizationsDelegates:
                        ThemasteroflawLocalizations.localizationsDelegates,
                    supportedLocales:
                        ThemasteroflawLocalizations.supportedLocales,
                    builder: (context, child) => AdminPanelFloatingHead(
                      child: OnPhoneShakeDevPanelLauncherWidget(
                        child: child ?? const SizedBox.shrink(),
                      ),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
