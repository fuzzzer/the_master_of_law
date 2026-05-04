import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryIconButton extends StatelessWidget {
  const PrimaryIconButton({
    super.key,
    this.height,
    this.width,
    this.borderRadiusValue,
    this.borderWidth = 1,
    this.maxLines = 1,
    this.buttonColor,
    this.borderColor,
    this.disabledButtonColor,
    this.disabledBorderColor,
    this.disabledLabelColor,
    this.iconWidget,
    this.isDisabled = false,
    this.onPressed,
  });

  final double? height;
  final double? width;
  final double? borderRadiusValue;
  final double borderWidth;
  final int maxLines;
  final Color? buttonColor;
  final Color? borderColor;
  final Color? disabledButtonColor;
  final Color? disabledBorderColor;
  final Color? disabledLabelColor;
  final Widget? iconWidget;
  final bool isDisabled;
  final void Function()? onPressed;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return PrimaryButton(
      buttonColor: buttonColor ?? uiColors.backgroundSecondaryColor,
      borderColor: borderColor ?? uiColors.backgroundSecondaryColor,
      disabledLabelColor: disabledLabelColor,
      disabledButtonColor: disabledButtonColor,
      disabledBorderColor: disabledBorderColor,
      borderRadiusValue: borderRadiusValue ?? 200,
      borderWidth: borderWidth,
      isDisabled: isDisabled,
      maxLines: maxLines,
      onPressed: onPressed,
      iconWidget: iconWidget,
      // width: width ?? 36,
      height: height ?? 36,
    );
  }
}
