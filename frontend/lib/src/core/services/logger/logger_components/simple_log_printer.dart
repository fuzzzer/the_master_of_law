// ignore_for_file: no_default_cases

import 'package:logger/logger.dart';

class SimpleLogPrinter extends LogPrinter {
  @override
  List<String> log(LogEvent event) {
    final emoji = _levelEmoji(event.level);
    final time = DateTime.now().toIso8601String();
    final message = '[$time] $emoji ${event.message}';

    return [
      message,
      '\n----------------------------------------\n',
    ];
  }

  String _levelEmoji(Level level) {
    switch (level) {
      case Level.trace:
        return '🔍 TRACE: ';
      case Level.debug:
        return '🐞 DEBUG: ';
      case Level.info:
        return '💡 INFO: ';
      case Level.warning:
        return '⚠️ WARN: ';
      case Level.error:
        return '❌ ERROR:';
      case Level.fatal:
        return '🔥 FATAL:';
      default:
        return 'LOG: ';
    }
  }
}
