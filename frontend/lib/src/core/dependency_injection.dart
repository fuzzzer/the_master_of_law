import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:package_info_plus/package_info_plus.dart';

// Conditional import: web has no file system, native does.
import 'dependency_injection_web.dart' if (dart.library.io) 'dependency_injection_native.dart' as platform_di;

class DependencyInjection {
  static Future<void> inject() async {
    final packageInfo = await PackageInfo.fromPlatform();

    // Register platform-specific directories (skipped on web).
    await platform_di.registerPlatformDependencies();

    sl.safeRegisterSingleton<PackageInfo>(packageInfo);

    sl.safeRegisterSingleton<SecureStorageService>(SecureStorageService(const FlutterSecureStorage()));

    final fuzzzyLawHttpClient = FuzzzyLawHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<FuzzzyLawHttpClient>(fuzzzyLawHttpClient);

    final fuzzzyLawPublicHttpClient = FuzzzyLawPublicHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<FuzzzyLawPublicHttpClient>(fuzzzyLawPublicHttpClient);
  }
}
