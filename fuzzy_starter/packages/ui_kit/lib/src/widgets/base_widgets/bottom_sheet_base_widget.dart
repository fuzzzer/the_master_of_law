import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class BottomSheetBaseWidget extends StatelessWidget {
  const BottomSheetBaseWidget({
    super.key,
    required this.bottomSheetHeader,
    required this.content,
    this.contentPadding = const EdgeInsets.all(20),
    this.heightFactor = 0.7,
    this.backgroundColor,
    this.bottomPadding = 0,
  });

  final Widget bottomSheetHeader;
  final Widget content;
  final EdgeInsets contentPadding;
  final double heightFactor;
  final Color? backgroundColor;
  final double bottomPadding;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final screenSize = MediaQuery.sizeOf(context);

    final maxSheetHeight = screenSize.height * heightFactor;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomPadding),
      child: ClipRRect(
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: 250,
            maxHeight: maxSheetHeight,
          ),
          child: Material(
            color: backgroundColor ?? uiColors.backgroundSecondaryColor,
            child: SizedBox(
              width: screenSize.width,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  bottomSheetHeader,
                  Padding(
                    padding: contentPadding,
                    child: content,
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
