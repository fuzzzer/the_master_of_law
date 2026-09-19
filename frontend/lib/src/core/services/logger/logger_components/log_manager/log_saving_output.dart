import 'package:flutter/foundation.dart';
import 'package:fuzzzy_law/src/core/services/logger/logger_components/log_manager/logger_manager.dart';
import 'package:logger/logger.dart';

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
