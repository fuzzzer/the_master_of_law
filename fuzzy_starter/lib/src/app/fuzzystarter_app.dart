import 'package:flutter/material.dart';
import 'package:fuzzystarter/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

class FuzzystarterApp extends StatelessWidget {
  const FuzzystarterApp({super.key});

  static Future<void> run() async {
    await Initializer.preAppInit();
    runApp(const FuzzystarterApp());
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
                    routerConfig: AppRouter.fuzzystarterRouter,
                    scaffoldMessengerKey: scaffoldMessengerKey,
                    theme: switch (themeBrightness) {
                      Brightness.dark => UiKitTheme.dark(),
                      Brightness.light => UiKitTheme.light(),
                    },
                    locale: Locale(locale.languageCode),
                    localizationsDelegates: FuzzystarterLocalizations.localizationsDelegates,
                    supportedLocales: FuzzystarterLocalizations.supportedLocales,
                    builder: (context, child) => OnPhoneShakeDevPanelLauncherWidget(
                      child: child ?? const SizedBox.shrink(),
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
