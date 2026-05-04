import 'dart:io';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:themasteroflaw/src/src.dart';

class DependencyInjection {
  static Future<void> inject() async {
    late final Directory documentsDirectory;
    late final Directory supportDirectory;

    late final PackageInfo packageInfo;

    await Future.wait<void>([
      (() async => documentsDirectory = await getApplicationDocumentsDirectory())(),
      (() async => supportDirectory = await getApplicationSupportDirectory())(),
      (() async => packageInfo = await PackageInfo.fromPlatform())(),
    ]);

    sl.safeRegisterSingleton<AppDocumentsDirectory>(AppDocumentsDirectory(directory: documentsDirectory));

    sl.safeRegisterSingleton<AppSupportDirectory>(AppSupportDirectory(directory: supportDirectory));

    sl.safeRegisterSingleton<PackageInfo>(packageInfo);

    sl.safeRegisterSingleton<SecureStorageService>(SecureStorageService(const FlutterSecureStorage()));

    final themasteroflawHttpClient = ThemasteroflawHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<ThemasteroflawHttpClient>(themasteroflawHttpClient);

    final themasteroflawPublicHttpClient = ThemasteroflawPublicHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<ThemasteroflawPublicHttpClient>(themasteroflawPublicHttpClient);
  }
}
