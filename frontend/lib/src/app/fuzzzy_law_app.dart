import 'package:flutter/material.dart';
import 'package:fuzzzy_law/src/src.dart';

class FuzzzyLawApp extends StatelessWidget {
  const FuzzzyLawApp({super.key});

  static Future<void> run() async {
    await Initializer.preAppInit();
    runApp(const FuzzzyLawApp());
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
                    routerConfig: AppRouter.fuzzzyLawRouter,
                    // No `scaffoldMessengerKey:` — the app-wide
                    // `GlobalKey<ScaffoldMessengerState>` that used to live at
                    // the top of this file was deleted at M12. M11 replaced
                    // every `SnackBar` with `FuzzzyToast.show`, which resolves
                    // its own overlay from the call-site context, so the key
                    // had zero readers. `MaterialApp` creates its own
                    // `ScaffoldMessenger` when none is supplied.
                    theme: switch (themeBrightness) {
                      Brightness.dark => FuzzzyLawTheme.dark(),
                      Brightness.light => FuzzzyLawTheme.light(),
                    },
                    locale: Locale(locale.languageCode),
                    localizationsDelegates:
                        FuzzzyLawLocalizations.localizationsDelegates,
                    supportedLocales:
                        FuzzzyLawLocalizations.supportedLocales,
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
