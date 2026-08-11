// exporter:ignore
//
// One half of the conditional import in
// `on_phone_shake_dev_panel_launcher_widget.dart`:
//   import 'shake_web.dart' if (dart.library.io) 'shake_native.dart' as shake_impl;
// Both halves declare `createShakeDetector` / `stopDetector`, so exporting
// both from `widgets.dart` is `ambiguous_export`. Marker honoured by
// `scripts/exporter.py` (EXPORTER_IGNORE_MARKER).

import 'package:shake/shake.dart';

/// Mobile implementation — uses actual accelerometer shake detection.
Object createShakeDetector({required void Function() onShake}) {
  return ShakeDetector.autoStart(
    onPhoneShake: (_) => onShake(),
  );
}

void stopDetector(Object detector) {
  (detector as ShakeDetector).stopListening();
}
