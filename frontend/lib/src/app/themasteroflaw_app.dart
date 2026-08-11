import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

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
                    scaffoldMessengerKey: scaffoldMessengerKey,
                    theme: switch (themeBrightness) {
                      Brightness.dark => ThemasteroflawTheme.dark(),
                      Brightness.light => ThemasteroflawTheme.light(),
                    },
                    locale: Locale(locale.languageCode),
                    localizationsDelegates: ThemasteroflawLocalizations.localizationsDelegates,
                    supportedLocales: ThemasteroflawLocalizations.supportedLocales,
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
