import 'package:logger/logger.dart';

class LogSaverInterceptor {
  final List<Level> logLevels;
  final void Function(Object? data, Level logLevelType) onLog;

  LogSaverInterceptor(this.onLog, {this.logLevels = const <Level>[]});

  void log(Object? data, Level logLevelType) {
    if (logLevels.isEmpty || logLevels.isNotEmpty && logLevels.contains(logLevelType)) {
      onLog(data, logLevelType);
    }
  }
}
