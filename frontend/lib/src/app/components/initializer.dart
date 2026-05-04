import 'package:bloc/bloc.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:logger/logger.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

class Initializer {
  static Future<void> preAppInit() async {
    WidgetsFlutterBinding.ensureInitialized();

    Bloc.observer = const AppBlocObserver();

    // Hive local storage
    await Hive.initFlutter();
    _registerHiveAdapters();

    await DependencyInjection.inject();

    await logger.initLogSaving(
      loggerLevel: kReleaseMode && appEnvironment.isProduction ? Level.error : Level.debug,
    );

    await SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
    ]);

    if (kReleaseMode) {
      ErrorWidget.builder = (FlutterErrorDetails details) {
        return const PrimaryErrorPageView(
          message: 'Unexpected App Crash',
        );
      };
    }

    await ApiCacheService().init();
  }

  static Future<void> postAppInit() async {}

  static void _registerHiveAdapters() {
    Hive
      ..registerAdapter(CaseDataAdapter())
      ..registerAdapter(FactDataAdapter())
      ..registerAdapter(ArgumentDataAdapter())
      ..registerAdapter(EvidenceDataAdapter())
      ..registerAdapter(StrategyDataAdapter())
      ..registerAdapter(TimelineEventDataAdapter())
      ..registerAdapter(RiskDataAdapter())
      ..registerAdapter(ActionItemDataAdapter());
  }
}
