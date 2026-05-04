import 'package:flutter/material.dart';

import '../../text_styles/text_styles.dart';

/// Theme extension for accessing text styles via `context.uiTextStyles`.
/// Wraps [UiKitTextStyles] getters into a theme-aware extension that supports
/// color application and theme lerping.
class UiTextStyles extends ThemeExtension<UiTextStyles> {
  // Display
  final TextStyle displayBold32;
  final TextStyle display32;

  // Headline
  final TextStyle headlineBold24;
  final TextStyle headline24;
  final TextStyle headlineBold20;
  final TextStyle headline20;

  // Title
  final TextStyle titleBold18;
  final TextStyle title18;

  // Body
  final TextStyle bodyBold16;
  final TextStyle body16;
  final TextStyle bodyBold14;
  final TextStyle body14;

  // Label
  final TextStyle labelBold14;
  final TextStyle label14;
  final TextStyle labelBold12;
  final TextStyle label12;

  // Caption
  final TextStyle caption11;

  // Legal
  final TextStyle legalCitation14;
  final TextStyle legalCitation12;
  final TextStyle legalBody16;
  final TextStyle legalBody14;

  UiTextStyles({
    TextStyle? displayBold32,
    TextStyle? display32,
    TextStyle? headlineBold24,
    TextStyle? headline24,
    TextStyle? headlineBold20,
    TextStyle? headline20,
    TextStyle? titleBold18,
    TextStyle? title18,
    TextStyle? bodyBold16,
    TextStyle? body16,
    TextStyle? bodyBold14,
    TextStyle? body14,
    TextStyle? labelBold14,
    TextStyle? label14,
    TextStyle? labelBold12,
    TextStyle? label12,
    TextStyle? caption11,
    TextStyle? legalCitation14,
    TextStyle? legalCitation12,
    TextStyle? legalBody16,
    TextStyle? legalBody14,
  })  : displayBold32 = displayBold32 ?? UiKitTextStyles.displayBold32,
        display32 = display32 ?? UiKitTextStyles.display32,
        headlineBold24 = headlineBold24 ?? UiKitTextStyles.headlineBold24,
        headline24 = headline24 ?? UiKitTextStyles.headline24,
        headlineBold20 = headlineBold20 ?? UiKitTextStyles.headlineBold20,
        headline20 = headline20 ?? UiKitTextStyles.headline20,
        titleBold18 = titleBold18 ?? UiKitTextStyles.titleBold18,
        title18 = title18 ?? UiKitTextStyles.title18,
        bodyBold16 = bodyBold16 ?? UiKitTextStyles.bodyBold16,
        body16 = body16 ?? UiKitTextStyles.body16,
        bodyBold14 = bodyBold14 ?? UiKitTextStyles.bodyBold14,
        body14 = body14 ?? UiKitTextStyles.body14,
        labelBold14 = labelBold14 ?? UiKitTextStyles.labelBold14,
        label14 = label14 ?? UiKitTextStyles.label14,
        labelBold12 = labelBold12 ?? UiKitTextStyles.labelBold12,
        label12 = label12 ?? UiKitTextStyles.label12,
        caption11 = caption11 ?? UiKitTextStyles.caption11,
        legalCitation14 = legalCitation14 ?? UiKitTextStyles.legalCitation14,
        legalCitation12 = legalCitation12 ?? UiKitTextStyles.legalCitation12,
        legalBody16 = legalBody16 ?? UiKitTextStyles.legalBody16,
        legalBody14 = legalBody14 ?? UiKitTextStyles.legalBody14;

  UiTextStyles apply({
    Color? color,
    double fontSizeFactor = 1,
  }) {
    return UiTextStyles(
      displayBold32: UiKitTextStyles.displayBold32.apply(color: color, fontSizeFactor: fontSizeFactor),
      display32: UiKitTextStyles.display32.apply(color: color, fontSizeFactor: fontSizeFactor),
      headlineBold24: UiKitTextStyles.headlineBold24.apply(color: color, fontSizeFactor: fontSizeFactor),
      headline24: UiKitTextStyles.headline24.apply(color: color, fontSizeFactor: fontSizeFactor),
      headlineBold20: UiKitTextStyles.headlineBold20.apply(color: color, fontSizeFactor: fontSizeFactor),
      headline20: UiKitTextStyles.headline20.apply(color: color, fontSizeFactor: fontSizeFactor),
      titleBold18: UiKitTextStyles.titleBold18.apply(color: color, fontSizeFactor: fontSizeFactor),
      title18: UiKitTextStyles.title18.apply(color: color, fontSizeFactor: fontSizeFactor),
      bodyBold16: UiKitTextStyles.bodyBold16.apply(color: color, fontSizeFactor: fontSizeFactor),
      body16: UiKitTextStyles.body16.apply(color: color, fontSizeFactor: fontSizeFactor),
      bodyBold14: UiKitTextStyles.bodyBold14.apply(color: color, fontSizeFactor: fontSizeFactor),
      body14: UiKitTextStyles.body14.apply(color: color, fontSizeFactor: fontSizeFactor),
      labelBold14: UiKitTextStyles.labelBold14.apply(color: color, fontSizeFactor: fontSizeFactor),
      label14: UiKitTextStyles.label14.apply(color: color, fontSizeFactor: fontSizeFactor),
      labelBold12: UiKitTextStyles.labelBold12.apply(color: color, fontSizeFactor: fontSizeFactor),
      label12: UiKitTextStyles.label12.apply(color: color, fontSizeFactor: fontSizeFactor),
      caption11: UiKitTextStyles.caption11.apply(color: color, fontSizeFactor: fontSizeFactor),
      legalCitation14: UiKitTextStyles.legalCitation14.apply(color: color, fontSizeFactor: fontSizeFactor),
      legalCitation12: UiKitTextStyles.legalCitation12.apply(color: color, fontSizeFactor: fontSizeFactor),
      legalBody16: UiKitTextStyles.legalBody16.apply(color: color, fontSizeFactor: fontSizeFactor),
      legalBody14: UiKitTextStyles.legalBody14.apply(color: color, fontSizeFactor: fontSizeFactor),
    );
  }

  @override
  ThemeExtension<UiTextStyles> lerp(ThemeExtension<UiTextStyles>? other, double t) {
    if (other is! UiTextStyles) return this;

    return UiTextStyles(
      displayBold32: TextStyle.lerp(displayBold32, other.displayBold32, t),
      display32: TextStyle.lerp(display32, other.display32, t),
      headlineBold24: TextStyle.lerp(headlineBold24, other.headlineBold24, t),
      headline24: TextStyle.lerp(headline24, other.headline24, t),
      headlineBold20: TextStyle.lerp(headlineBold20, other.headlineBold20, t),
      headline20: TextStyle.lerp(headline20, other.headline20, t),
      titleBold18: TextStyle.lerp(titleBold18, other.titleBold18, t),
      title18: TextStyle.lerp(title18, other.title18, t),
      bodyBold16: TextStyle.lerp(bodyBold16, other.bodyBold16, t),
      body16: TextStyle.lerp(body16, other.body16, t),
      bodyBold14: TextStyle.lerp(bodyBold14, other.bodyBold14, t),
      body14: TextStyle.lerp(body14, other.body14, t),
      labelBold14: TextStyle.lerp(labelBold14, other.labelBold14, t),
      label14: TextStyle.lerp(label14, other.label14, t),
      labelBold12: TextStyle.lerp(labelBold12, other.labelBold12, t),
      label12: TextStyle.lerp(label12, other.label12, t),
      caption11: TextStyle.lerp(caption11, other.caption11, t),
      legalCitation14: TextStyle.lerp(legalCitation14, other.legalCitation14, t),
      legalCitation12: TextStyle.lerp(legalCitation12, other.legalCitation12, t),
      legalBody16: TextStyle.lerp(legalBody16, other.legalBody16, t),
      legalBody14: TextStyle.lerp(legalBody14, other.legalBody14, t),
    );
  }

  @override
  UiTextStyles copyWith({
    TextStyle? displayBold32,
    TextStyle? display32,
    TextStyle? headlineBold24,
    TextStyle? headline24,
    TextStyle? headlineBold20,
    TextStyle? headline20,
    TextStyle? titleBold18,
    TextStyle? title18,
    TextStyle? bodyBold16,
    TextStyle? body16,
    TextStyle? bodyBold14,
    TextStyle? body14,
    TextStyle? labelBold14,
    TextStyle? label14,
    TextStyle? labelBold12,
    TextStyle? label12,
    TextStyle? caption11,
    TextStyle? legalCitation14,
    TextStyle? legalCitation12,
    TextStyle? legalBody16,
    TextStyle? legalBody14,
  }) {
    return UiTextStyles(
      displayBold32: displayBold32 ?? this.displayBold32,
      display32: display32 ?? this.display32,
      headlineBold24: headlineBold24 ?? this.headlineBold24,
      headline24: headline24 ?? this.headline24,
      headlineBold20: headlineBold20 ?? this.headlineBold20,
      headline20: headline20 ?? this.headline20,
      titleBold18: titleBold18 ?? this.titleBold18,
      title18: title18 ?? this.title18,
      bodyBold16: bodyBold16 ?? this.bodyBold16,
      body16: body16 ?? this.body16,
      bodyBold14: bodyBold14 ?? this.bodyBold14,
      body14: body14 ?? this.body14,
      labelBold14: labelBold14 ?? this.labelBold14,
      label14: label14 ?? this.label14,
      labelBold12: labelBold12 ?? this.labelBold12,
      label12: label12 ?? this.label12,
      caption11: caption11 ?? this.caption11,
      legalCitation14: legalCitation14 ?? this.legalCitation14,
      legalCitation12: legalCitation12 ?? this.legalCitation12,
      legalBody16: legalBody16 ?? this.legalBody16,
      legalBody14: legalBody14 ?? this.legalBody14,
    );
  }
}
