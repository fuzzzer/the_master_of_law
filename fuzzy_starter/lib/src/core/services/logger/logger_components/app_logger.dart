import 'package:flutter/foundation.dart';
import 'package:fuzzystarter/src/src.dart';
import 'package:logger/logger.dart';

class AppLogger {
  static Logger _logger = Logger(
    filter: ProductionFilter(),
    printer: SimpleLogPrinter(),
  );

  static late final LogManager logManager;
  static bool _isInitialized = false;

  static final ValueNotifier<Level> loggerLevelThreshold = ValueNotifier(Level.error);
  static final ValueNotifier<bool> savingAllLogsWithOutputIntercepting = ValueNotifier(false);

  AppLogger();

  Future<void> initLogSaving({
    required Level loggerLevel,
    bool forceInitLogger = false,
    bool savingAllLogs = false,
  }) async {
    if (_isInitialized && !forceInitLogger) {
      return;
    }

    if (!_isInitialized) {
      logManager = await LogManager.create(
        appStoragePath: sl.get<AppSupportDirectory>().directory.path,
      );
    }

    _logger = Logger(
      filter: ProductionFilter(),
      printer: SimpleLogPrinter(),
      output: savingAllLogs
          ? LogSavingOutput(
              logManager: logManager,
            )
          : null,
      level: loggerLevel,
    );

    loggerLevelThreshold.value = loggerLevel;
    savingAllLogsWithOutputIntercepting.value = savingAllLogs;

    _isInitialized = true;
  }

  void t(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.t(message, error: error, stackTrace: stackTrace, time: time);

  void d(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.d(message, error: error, stackTrace: stackTrace, time: time);

  void i(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.i(message, error: error, stackTrace: stackTrace, time: time);

  void w(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.w(message, error: error, stackTrace: stackTrace, time: time);

  void e(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.e(message, error: error, stackTrace: stackTrace, time: time);

  void f(
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.f(message, error: error, stackTrace: stackTrace, time: time);

  void log(
    Level level,
    dynamic message, {
    DateTime? time,
    Object? error,
    StackTrace? stackTrace,
  }) => _logger.log(level, message, error: error, stackTrace: stackTrace, time: time);
}
