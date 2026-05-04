import 'dart:io';

//stores logs by days not to overwhelm users device and control expired logs
class LogStorageService {
  late final String logsPath; // Directory where log files are stored
  static const maxLogFiles = 5; // Maximum number of log files to keep
  static const maxLogFileSize = 1024 * 1024; // Maximum log file size in bytes (1MB)
  static const dividerPattern = '{{*}}';

  LogStorageService({
    required String appStoragePath,
  }) {
    logsPath = '$appStoragePath/logs';
  }

  Future<void> saveLog(String logMessage) async {
    final filePath = _getFilePathByDay();
    final logFile = File(filePath);

    if (!await logFile.exists()) {
      await logFile.create(recursive: true);
    }

    final sink = logFile.openWrite(mode: FileMode.append);
    sink.write('$logMessage$dividerPattern');
    await sink.flush();
    await sink.close();

    await _orginizeLogsIfNeeded(logFile);
  }

  Future<List<String>> readLogs({
    int filesToRead = 1,
  }) async {
    final logsDirectory = Directory('$logsPath/');

    if (!(await logsDirectory.exists())) {
      await logsDirectory.create(recursive: true);
    }

    final logFiles = logsDirectory.listSync();

    logFiles.sort((a, b) => a.path.compareTo(b.path));

    final logList = <String>[];

    int filesRead = 0;

    for (int i = logFiles.length - 1; filesRead < filesToRead && i >= 0; i--) {
      final file = File(logFiles[i].path);

      final logsFromFile = (await file.readAsString()).split(dividerPattern).reversed;

      logList.addAll(logsFromFile);

      filesRead++;
    }

    return logList;
  }

  Future<void> clearLogs() async {
    final logFiles = Directory(logsPath).listSync();

    for (final element in logFiles) {
      await element.delete();
    }
  }

  String _getFilePathByDay() {
    final now = DateTime.now();
    final fileName = '${now.year}-${now.month}-${now.day}_$maxLogFiles.txt';
    return '$logsPath/$fileName';
  }

  Future<void> _orginizeLogsIfNeeded(File logFile) async {
    await _renameLogFilesIfNeeded(logFile);
    await _rotateLogsIfNeeded();
  }

  Future<void> _renameLogFilesIfNeeded(File currentFile) async {
    if (await currentFile.length() > maxLogFileSize) {
      await _renameLogFile(currentFile);
    }
  }

  Future<void> _renameLogFile(File currentFile) async {
    final now = DateTime.now();
    final currentFilePath = currentFile.path;

    final indexWhereIndexingStarts = currentFilePath.lastIndexOf('_') + 1;
    final indexWhereIndexingEnds = currentFilePath.lastIndexOf('.') - 1;

    final index = currentFilePath.substring(indexWhereIndexingStarts, indexWhereIndexingEnds + 1);

    int indexNumber = int.tryParse(index) ?? now.millisecondsSinceEpoch;
    indexNumber--;

    final fileBasePath = currentFilePath.substring(0, indexWhereIndexingStarts);

    final newFileName = '$fileBasePath$indexNumber.txt';

    final newFilePath = '$logsPath/$newFileName';

    await currentFile.rename(newFilePath);
  }

  Future<void> _rotateLogsIfNeeded() async {
    final logFiles = Directory(logsPath).listSync();

    if (logFiles.length > maxLogFiles) {
      logFiles.sort((a, b) => a.path.compareTo(b.path));
      for (int i = 0; i < logFiles.length - maxLogFiles; i++) {
        await logFiles[i].delete();
      }
    }
  }
}
