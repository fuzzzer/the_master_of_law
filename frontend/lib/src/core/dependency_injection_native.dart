import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:themasteroflaw/src/src.dart';

/// Mobile/Desktop — registers real file system directories.
Future<void> registerPlatformDependencies() async {
  late final Directory documentsDirectory;
  late final Directory supportDirectory;

  await Future.wait<void>([
    (() async => documentsDirectory = await getApplicationDocumentsDirectory())(),
    (() async => supportDirectory = await getApplicationSupportDirectory())(),
  ]);

  sl.safeRegisterSingleton<AppDocumentsDirectory>(AppDocumentsDirectory(directory: documentsDirectory));
  sl.safeRegisterSingleton<AppSupportDirectory>(AppSupportDirectory(directory: supportDirectory));
}
