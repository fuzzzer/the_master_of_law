import 'package:flutter/material.dart';

class DevPanelPreviewOverlay extends StatefulWidget {
  final Size screenSize;
  final EdgeInsets screenPadding;
  const DevPanelPreviewOverlay({
    super.key,
    required this.screenSize,
    this.screenPadding = EdgeInsets.zero,
  });

  @override
  State<DevPanelPreviewOverlay> createState() => _DevPanelPreviewOverlayState();
}

class _DevPanelPreviewOverlayState extends State<DevPanelPreviewOverlay> {
  final double startingTop = 100;
  late double endingTop;

  final double widgetSize = 90;

  late double landscapeRightPadding;

  late double screenWidth;
  late double screenHeight;

  late double top;
  late double left;

  @override
  void didUpdateWidget(DevPanelPreviewOverlay activeExamOverlay) {
    final bottomNavigationHeight = widget.screenSize.aspectRatio > 1.2 ? 40 : 70;

    endingTop = bottomNavigationHeight + widget.screenPadding.bottom;

    screenWidth = widget.screenSize.width;
    screenHeight = widget.screenSize.height;

    landscapeRightPadding = widget.screenPadding.left + widget.screenPadding.right;

    left = screenWidth - widgetSize - landscapeRightPadding;
    top = screenHeight / 2;

    super.didUpdateWidget(activeExamOverlay);
  }

  @override
  void initState() {
    final bottomNavigationHeight = widget.screenSize.aspectRatio > 1.2 ? 40 : 70;

    endingTop = bottomNavigationHeight + widget.screenPadding.bottom;

    screenWidth = widget.screenSize.width;
    screenHeight = widget.screenSize.height;

    landscapeRightPadding = widget.screenPadding.left + widget.screenPadding.right;

    left = screenWidth - widgetSize - landscapeRightPadding;
    top = screenHeight / 2;

    super.initState();
  }

  void onPanUpdate(DragUpdateDetails details) {
    final globalX = details.globalPosition.dx;
    final globalY = details.globalPosition.dy;

    if (globalX > 0 && globalX < screenWidth && globalY > startingTop && globalY < screenHeight - endingTop) {
      final deltaX = details.delta.dx;
      final deltaY = details.delta.dy;

      final newLeft = left + deltaX;
      final newTop = top + deltaY;

      setState(() {
        if (newLeft > 0 && newLeft < screenWidth - widgetSize - landscapeRightPadding) {
          left = newLeft;
        }

        if (newTop > startingTop && newTop < screenHeight - endingTop - widgetSize) {
          top = newTop;
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      width: widgetSize,
      height: widgetSize,
      top: top - widgetSize,
      left: left,
      child: GestureDetector(
        onTap: () {},
        onPanUpdate: onPanUpdate,
        child: Material(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(
              widgetSize / 2,
            ),
            side: const BorderSide(
              width: 2,
              color: Colors.green,
            ),
          ),
          elevation: 10,
          child: Container(
            decoration: const BoxDecoration(shape: BoxShape.circle, color: Colors.grey),
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.assignment_outlined,
                    size: 26,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
