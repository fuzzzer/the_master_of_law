import 'dart:isolate';

import 'log_storage_service.dart';

// logIsolateSendPort: Used to send messages from the main isolate to the log isolate.
// logIsolateReceivePort: Used to receive messages from the main isolate in the log isolate.

// mainIsolateReceivePort: Used only once to receive the logIsolateSendPort as the first message.
// mainIsolateSendPort: Used only once to send the logIsolateSendPort as the first message. for main isolate to have access to sending messages to log isolate
class LogManager {
  //used to send messages to the log isolate, messaging is one directional used to send the isolate app's logs. Only added so storing logs with some logic is done on separate isolate since it is heavy operation
  final SendPort _logIsolateSendPort;
  final String _appStoragePath;

  LogManager._(this._logIsolateSendPort, this._appStoragePath);

  static Future<LogManager> create({required String appStoragePath}) async {
    final ReceivePort mainIsolateReceivePort = ReceivePort();
    final mainIsolateSendPort = mainIsolateReceivePort.sendPort;

    await Isolate.spawn(
      _logIsolateMain,
      LogIsolateInitializationData(
        mainIsolateSendPort: mainIsolateSendPort,
        appStoragePath: appStoragePath,
      ),
    );

    final SendPort logIsolateSendPort = await mainIsolateReceivePort.first as SendPort;

    return LogManager._(logIsolateSendPort, appStoragePath);
  }

  static Future<void> _logIsolateMain(LogIsolateInitializationData initializationData) async {
    final ReceivePort logIsolateReceivePort = ReceivePort();

    initializationData.mainIsolateSendPort.send(logIsolateReceivePort.sendPort);

    final logStorageService = LogStorageService(appStoragePath: initializationData.appStoragePath);

    logIsolateReceivePort.listen((message) {
      final String log = message['log'] as String;

      logStorageService.saveLog(log);
    });
  }

  void saveLog(String logRecord) {
    _logIsolateSendPort.send({'log': '${DateTime.now()}: $logRecord'});
  }

  Future<void> clearLogs() async {
    final logStorageService = LogStorageService(appStoragePath: _appStoragePath);

    await logStorageService.clearLogs();
  }
}

class LogIsolateInitializationData {
  final SendPort mainIsolateSendPort;
  final String appStoragePath;

  LogIsolateInitializationData({
    required this.mainIsolateSendPort,
    required this.appStoragePath,
  });
}
