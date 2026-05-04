import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:themasteroflaw/src/core/services/logger/logger_components/log_manager/logger_manager.dart';

class LogSavingOutput extends LogOutput {
  final LogManager logManager;
  final ConsoleOutput _console = ConsoleOutput();

  LogSavingOutput({
    required this.logManager,
  });

  @override
  void output(OutputEvent event) {
    logManager.saveLog(event.lines.join());

    if (kDebugMode) {
      _console.output(event);
    }
  }
}
