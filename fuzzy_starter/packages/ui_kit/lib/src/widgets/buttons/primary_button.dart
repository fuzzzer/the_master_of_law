import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
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
    this.isLoading = false,
    this.onPressed,
    this.contentPadding = const EdgeInsets.symmetric(horizontal: 20.0),
    this.contentBasedWidth = false
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
  final bool isLoading;
  final void Function()? onPressed;
  final EdgeInsets contentPadding;
  final bool contentBasedWidth;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;
    final uiFormStyles = theme.extension<UiFormStyles>()!;

    final buttonHeight = height ?? uiFormStyles.buttonHeight;
    final buttonWidth = width ?? uiFormStyles.buttonWidth;
    final buttonBackgroundColor = buttonColor ?? uiColors.primaryColor;
    final disabledButtonBackgroundColor = disabledButtonColor ?? uiColors.secondaryColor;
    final buttonBorderRadiusValue = borderRadiusValue ?? uiFormStyles.borderRadiusValue;
    final buttonBorderColor = borderColor ?? uiColors.backgroundPrimaryColor;
    final disabledButtonBorderColor = disabledBorderColor ?? uiColors.backgroundSecondaryColor;

    final buttonTextStyle = (labelStyle ?? uiTextStyles.body16).copyWith(
      color: labelColor ?? uiColors.primaryColor,
    );
    final disabledButtonTextStyle = (labelStyle ?? uiTextStyles.body16).copyWith(
      color: disabledLabelColor ?? uiColors.secondaryColor,
    );

    final buttonBorderRadius = BorderRadius.all(Radius.circular(buttonBorderRadiusValue));

    return Material(
      color: isDisabled || isLoading ? disabledButtonBackgroundColor : buttonBackgroundColor,
      borderRadius: buttonBorderRadius,
      child: InkWell(
        onTap: isDisabled ? null : onPressed,
        borderRadius: buttonBorderRadius,
        child: DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: buttonBorderRadius,
            border: Border.all(color: isDisabled ? disabledButtonBorderColor : buttonBorderColor, width: borderWidth),
          ),
          child: SizedBox(
            width: contentBasedWidth ? null : buttonWidth,
            height: buttonHeight,
            child: Padding(
              padding: contentPadding,
              child: isLoading
                  ? Center(
                      child: SizedBox.square(
                        dimension: 24,
                        child: PrimaryLoader(),
                      ),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      spacing: uiFormStyles.rowSpacing,
                      children: [
                        if (iconWidget != null) iconWidget!,
                        if (label != null)
                          Flexible(
                            child: Text(
                              label!,
                              textAlign: TextAlign.center,
                              style: isDisabled ? disabledButtonTextStyle : buttonTextStyle,
                              maxLines: maxLines,
                              overflow: TextOverflow.ellipsis,
                            ),
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
