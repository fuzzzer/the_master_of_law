import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:fuzzzy_law/src/core/services/dev_panel/ui/screens/dev_panel_screen.dart';
import 'package:fuzzzy_law/src/core/services/dev_panel/ui/ui.dart';

// Conditionally import shake — only on native platforms with accelerometer.
import 'shake_web.dart' if (dart.library.io) 'shake_native.dart' as shake_impl;

class OnPhoneShakeDevPanelLauncherWidget extends StatefulWidget {
  const OnPhoneShakeDevPanelLauncherWidget({
    super.key,
    required this.child,
  });

  final Widget child;

  @override
  State<OnPhoneShakeDevPanelLauncherWidget> createState() => _OnPhoneShakeDevPanelLauncherWidgetState();
}

class _OnPhoneShakeDevPanelLauncherWidgetState extends State<OnPhoneShakeDevPanelLauncherWidget> {
  Object? _detector;

  @override
  void initState() {
    super.initState();
    if (!kIsWeb) {
      _detector = shake_impl.createShakeDetector(onShake: openDevPanel);
    }
  }

  @override
  void dispose() {
    if (_detector != null) {
      shake_impl.stopDetector(_detector!);
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
