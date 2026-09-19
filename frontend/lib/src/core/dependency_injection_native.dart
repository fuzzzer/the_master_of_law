// exporter:ignore
//
// One half of the conditional import in `dependency_injection.dart`:
//   import 'dependency_injection_web.dart'
//       if (dart.library.io) 'dependency_injection_native.dart' as platform_di;
// Both halves declare `registerPlatformDependencies` — that is the whole
// mechanism. Exporting both from `core.dart` is `ambiguous_export` and the
// app stops compiling, so `./exp.sh` must skip this file. Marker honoured by
// `scripts/exporter.py` (EXPORTER_IGNORE_MARKER). Import it only through the
// conditional import above, never directly.

import 'dart:io';

import 'package:fuzzzy_law/src/src.dart';
import 'package:path_provider/path_provider.dart';

/// Mobile/Desktop — registers real file system directories.
Future<void> registerPlatformDependencies() async {
  late final Directory documentsDirectory;
  late final Directory supportDirectory;

  await Future.wait<void>([
    (() async =>
        documentsDirectory = await getApplicationDocumentsDirectory())(),
    (() async => supportDirectory = await getApplicationSupportDirectory())(),
  ]);

  sl.safeRegisterSingleton<AppDocumentsDirectory>(
    AppDocumentsDirectory(directory: documentsDirectory),
  );
  sl.safeRegisterSingleton<AppSupportDirectory>(
    AppSupportDirectory(directory: supportDirectory),
  );
}
