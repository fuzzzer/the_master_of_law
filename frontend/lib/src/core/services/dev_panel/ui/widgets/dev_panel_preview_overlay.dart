import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

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
    final bottomNavigationHeight = widget.screenSize.aspectRatio > 1.2
        ? 40
        : 70;

    endingTop = bottomNavigationHeight + widget.screenPadding.bottom;

    screenWidth = widget.screenSize.width;
    screenHeight = widget.screenSize.height;

    landscapeRightPadding =
        widget.screenPadding.left + widget.screenPadding.right;

    left = screenWidth - widgetSize - landscapeRightPadding;
    top = screenHeight / 2;

    super.didUpdateWidget(activeExamOverlay);
  }

  @override
  void initState() {
    final bottomNavigationHeight = widget.screenSize.aspectRatio > 1.2
        ? 40
        : 70;

    endingTop = bottomNavigationHeight + widget.screenPadding.bottom;

    screenWidth = widget.screenSize.width;
    screenHeight = widget.screenSize.height;

    landscapeRightPadding =
        widget.screenPadding.left + widget.screenPadding.right;

    left = screenWidth - widgetSize - landscapeRightPadding;
    top = screenHeight / 2;

    super.initState();
  }

  void onPanUpdate(DragUpdateDetails details) {
    final globalX = details.globalPosition.dx;
    final globalY = details.globalPosition.dy;

    if (globalX > 0 &&
        globalX < screenWidth &&
        globalY > startingTop &&
        globalY < screenHeight - endingTop) {
      final deltaX = details.delta.dx;
      final deltaY = details.delta.dy;

      final newLeft = left + deltaX;
      final newTop = top + deltaY;

      setState(() {
        if (newLeft > 0 &&
            newLeft < screenWidth - widgetSize - landscapeRightPadding) {
          left = newLeft;
        }

        if (newTop > startingTop &&
            newTop < screenHeight - endingTop - widgetSize) {
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
        child: Builder(
          builder: (context) {
            final colors = context.fuzzzyColors;
            return Material(
              // Rung 3 of the ladder: this disc FLOATS over the whole app, so
              // it is `raised` inside a `lineStrong` outline. The fork used
              // `Colors.green` for the ring and `Colors.grey` for the fill —
              // two Material hues chosen to be conspicuous during development,
              // which is exactly what `raised` + `lineStrong` says in roles.
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(widgetSize / 2),
                side: BorderSide(width: 2, color: colors.lineStrong),
              ),
              // `elevation: 10` DELETED, not set to 0: Ink's elevation step is
              // the BORDER, not a shadow (MAPPING §6), and `Material` already
              // defaults to 0 — restating it trips `avoid_redundant_argument_
              // values`. Contrast `PopupMenuButton` (M7 §8), which defaults to
              // a shadow and therefore must have `elevation: 0` set explicitly.
              color: colors.raised,
              child: Center(
                child: Icon(
                  Icons.assignment_outlined,
                  // Dimension: the handle's glyph inside a 90px disc.
                  size: 26,
                  color: colors.ink,
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
