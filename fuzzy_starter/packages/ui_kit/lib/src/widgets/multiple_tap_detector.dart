import 'package:flutter/widgets.dart';

class MultipleTapDetector extends StatefulWidget {
  const MultipleTapDetector({
    super.key,
    required this.child,
    required this.onMultipleTap,
    this.tapCount = 5,
    this.maxTapIntervalSeconds = 1,
  });

  final Widget child;
  final void Function() onMultipleTap;
  final int tapCount;
  final int maxTapIntervalSeconds;

  @override
  State<MultipleTapDetector> createState() => _MultipleTapDetectorState();
}

class _MultipleTapDetectorState extends State<MultipleTapDetector> {
  int tapCount = 0;
  DateTime? previousTapTime;

  void handleTap() {
    final currentTime = DateTime.now();

    if (previousTapTime == null) {
      setState(() {
        previousTapTime = currentTime;
        tapCount = 1;
      });

      return;
    }

    if (currentTime.difference(previousTapTime!).inSeconds > 1) {
      setState(() {
        previousTapTime = currentTime;
        tapCount = 1;
      });
    } else {
      setState(() {
        tapCount++;
      });

      if (tapCount == widget.tapCount) {
        widget.onMultipleTap();
        setState(() {
          previousTapTime = null;
          tapCount = 0;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: handleTap,
      child: widget.child,
    );
  }
}
