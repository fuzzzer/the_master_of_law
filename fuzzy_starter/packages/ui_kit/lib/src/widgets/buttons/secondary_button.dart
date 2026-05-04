import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class SecondaryButton extends StatelessWidget {
  const SecondaryButton({
    super.key,
    this.label,
    this.labelStyle,
    this.height,
    this.width,
    this.borderRadiusValue,
    this.borderWidth = 1,
    this.maxLines = 1,
    this.buttonColor,
    this.borderColor,
    this.labelColor,
    this.disabledButtonColor,
    this.disabledBorderColor,
    this.disabledLabelColor,
    this.iconWidget,
    this.isDisabled = false,
    this.onPressed,
    this.contentBasedWidth = false,
  });

  final String? label;
  final TextStyle? labelStyle;
  final double? height;
  final double? width;
  final double? borderRadiusValue;
  final double borderWidth;
  final int maxLines;
  final Color? buttonColor;
  final Color? borderColor;
  final Color? labelColor;
  final Color? disabledButtonColor;
  final Color? disabledBorderColor;
  final Color? disabledLabelColor;
  final Widget? iconWidget;
  final bool isDisabled;
  final void Function()? onPressed;
  final bool contentBasedWidth;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return PrimaryButton(
      buttonColor: buttonColor ?? uiColors.secondaryColor,
      borderColor: borderColor ?? uiColors.secondaryColor,
      disabledLabelColor: disabledLabelColor,
      disabledButtonColor: disabledButtonColor,
      disabledBorderColor: disabledBorderColor,
      borderRadiusValue: borderRadiusValue,
      borderWidth: borderWidth,
      height: height,
      isDisabled: isDisabled,
      label: label,
      labelColor: labelColor,
      labelStyle: labelStyle,
      maxLines: maxLines,
      onPressed: onPressed,
      iconWidget: iconWidget,
      width: width,
      contentBasedWidth: contentBasedWidth,
    );
  }
}
