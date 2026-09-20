// exporter:ignore
//
// The web half of `dependency_injection.dart`'s conditional import. See the
// banner in `dependency_injection_native.dart` for why this must not be
// exported from `core.dart`.

/// Web platform — file system directories are not available.
/// Dev panel logs and file export are no-ops on web.
Future<void> registerPlatformDependencies() async {}
