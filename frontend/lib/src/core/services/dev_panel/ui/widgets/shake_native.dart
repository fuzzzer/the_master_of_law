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
