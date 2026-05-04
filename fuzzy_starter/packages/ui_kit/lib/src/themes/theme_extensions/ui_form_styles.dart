import 'dart:ui';
import 'package:flutter/material.dart';

class UiFormStyles extends ThemeExtension<UiFormStyles> {
  final double borderRadiusValue;
  final double buttonHeight;
  final double buttonWidth;
  final double rowSpacing;
  final double columnSpacing;
  final EdgeInsets widgetContentPadding;
  final EdgeInsets scrollPadding;
  final EdgeInsets screenContentPadding;
  final double screenContentPrimaryHorizontalGap;

  const UiFormStyles({
    required this.borderRadiusValue,
    required this.buttonHeight,
    required this.buttonWidth,
    required this.rowSpacing,
    required this.columnSpacing,
    required this.widgetContentPadding,
    required this.scrollPadding,
    required this.screenContentPadding,
    required this.screenContentPrimaryHorizontalGap,
  });

  const UiFormStyles.original()
    : borderRadiusValue = 200,
      buttonHeight = 50,
      buttonWidth = double.maxFinite,
      rowSpacing = 8,
      columnSpacing = 12,
      widgetContentPadding = const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      scrollPadding = const EdgeInsets.all(20),
      screenContentPadding = const EdgeInsets.symmetric(horizontal: 20),
      screenContentPrimaryHorizontalGap = 16;

  @override
  UiFormStyles copyWith({
    double? borderRadiusValue,
    double? buttonHeight,
    double? buttonWidth,
    double? rowSpacing,
    double? columnSpacing,
    EdgeInsets? widgetContentPadding,
    EdgeInsets? scrollPadding,
    EdgeInsets? screenContentPadding,
    double? screenContentPrimaryHorizontalGap,
  }) {
    return UiFormStyles(
      borderRadiusValue: borderRadiusValue ?? this.borderRadiusValue,
      buttonHeight: buttonHeight ?? this.buttonHeight,
      buttonWidth: buttonWidth ?? this.buttonWidth,
      rowSpacing: rowSpacing ?? this.rowSpacing,
      columnSpacing: columnSpacing ?? this.columnSpacing,
      widgetContentPadding: widgetContentPadding ?? this.widgetContentPadding,
      scrollPadding: scrollPadding ?? this.scrollPadding,
      screenContentPadding: screenContentPadding ?? this.screenContentPadding,
      screenContentPrimaryHorizontalGap: screenContentPrimaryHorizontalGap ?? this.screenContentPrimaryHorizontalGap,
    );
  }

  @override
  UiFormStyles lerp(ThemeExtension<UiFormStyles>? other, double t) {
    if (other is! UiFormStyles) return this;
    return UiFormStyles(
      borderRadiusValue: lerpDouble(borderRadiusValue, other.borderRadiusValue, t)!,
      buttonHeight: lerpDouble(buttonHeight, other.buttonHeight, t)!,
      buttonWidth: lerpDouble(buttonWidth, other.buttonWidth, t)!,
      rowSpacing: lerpDouble(rowSpacing, other.rowSpacing, t) ?? rowSpacing,
      columnSpacing: lerpDouble(columnSpacing, other.columnSpacing, t)!,
      widgetContentPadding: t < 0.5 ? widgetContentPadding : other.widgetContentPadding,
      scrollPadding: t < 0.5 ? scrollPadding : other.scrollPadding,
      screenContentPadding: t < 0.5 ? screenContentPadding : other.screenContentPadding,
      screenContentPrimaryHorizontalGap:
          lerpDouble(screenContentPrimaryHorizontalGap, other.screenContentPrimaryHorizontalGap, t) ??
          screenContentPrimaryHorizontalGap,
    );
  }
}
