// exporter:ignore
//
// The web half of the shake-detector conditional import. See the banner in
// `shake_native.dart`.

/// Web stub — no shake detection available on web.
Object? createShakeDetector({required void Function() onShake}) => null;
void stopDetector(Object detector) {}
