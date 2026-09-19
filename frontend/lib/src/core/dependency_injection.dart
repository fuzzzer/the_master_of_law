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

    // Registered before the http clients: the auth interceptor reads the
    // device id on every outgoing request, so it must already exist by the
    // time the first one is built.
    sl.safeRegisterSingleton<DeviceIdService>(
      DeviceIdService(sl.get<SecureStorageService>()),
    );

    // Loaded eagerly so the auth interceptor can read the chosen models
    // synchronously on every request instead of awaiting secure storage.
    final modelPreferences = ModelPreferenceService(sl.get<SecureStorageService>());
    await modelPreferences.load();
    sl.safeRegisterSingleton<ModelPreferenceService>(modelPreferences);

    final fuzzzyLawHttpClient = FuzzzyLawHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<FuzzzyLawHttpClient>(fuzzzyLawHttpClient);

    final fuzzzyLawPublicHttpClient = FuzzzyLawPublicHttpClient(packageInfo: packageInfo);
    sl.safeRegisterSingleton<FuzzzyLawPublicHttpClient>(fuzzzyLawPublicHttpClient);
  }
}
