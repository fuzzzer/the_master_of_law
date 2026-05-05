import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:themasteroflaw/src/src.dart';

// Conditional import: web has no file system, native does.
import 'dependency_injection_web.dart' if (dart.library.io) 'dependency_injection_native.dart' as platform_di;

class DependencyInjection {
  static Future<void> inject() async {
    final packageInfo = await PackageInfo.fromPlatform();

    // Register platform-specific directories (skipped on web).
    await platform_di.registerPlatformDependencies();

    sl.safeRegisterSingleton<PackageInfo>(packageInfo);

    sl.safeRegisterSingleton<SecureStorageService>(SecureStorageService(const FlutterSecureStorage()));

    final themasteroflawHttpClient = ThemasteroflawHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<ThemasteroflawHttpClient>(themasteroflawHttpClient);

    final themasteroflawPublicHttpClient = ThemasteroflawPublicHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<ThemasteroflawPublicHttpClient>(themasteroflawPublicHttpClient);
  }
}
