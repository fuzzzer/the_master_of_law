import 'package:flutter/widgets.dart';
import 'package:fuzzystarter/src/core/services/dev_panel/ui/screens/dev_panel_screen.dart';
import 'package:fuzzystarter/src/core/services/dev_panel/ui/ui.dart';
import 'package:shake/shake.dart';

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
  ShakeDetector? _detector;

  @override
  void initState() {
    super.initState();
    _detector = ShakeDetector.autoStart(
      onPhoneShake: onPhoneShake,
    );
  }

  void onPhoneShake(ShakeEvent shakeEvent) {
    openDevPanel();
  }

  @override
  void dispose() {
    _detector?.stopListening();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
