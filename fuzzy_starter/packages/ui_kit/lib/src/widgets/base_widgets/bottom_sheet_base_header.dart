import 'package:flutter/material.dart';

class BottomSheetBaseHeader extends StatelessWidget {
  const BottomSheetBaseHeader({
    super.key,
    required this.icon,
    required this.label,
    this.onCloseTapped,
    this.hasAutomaticCloseAction = true,
  });

  final Widget icon;
  final String label;
  final VoidCallback? onCloseTapped;
  final bool hasAutomaticCloseAction;

  @override
  Widget build(BuildContext context) {
    // final theme = Theme.of(context);
    // final uiColors = theme.extension<UiColors>()!;
    // final uiTextStyles = theme.extension<UiTextStyles>()!;

    // const closeButtonDimension = 30.0;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        //TODO add bottom sheet header
        Divider(
          height: 1,
          thickness: 1,
        ),
      ],
    );
  }
}
