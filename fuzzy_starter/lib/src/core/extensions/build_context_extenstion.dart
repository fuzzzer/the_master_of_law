import 'package:flutter/material.dart';
import 'package:fuzzystarter/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

// Use this wisely, when reusing same inherited preferences in the widget.
// for example: calling context.uiColors 10 times in a single widget, would trigger multiple Theme.of(context) lookups.
// for heavy widgets try to save the references like:
// final uiColors = context.uiColors;
// final uiTextStyles = context.uiTextStyles;
// final uiFormStyles = context.uiTextStyles;
// etc ...
extension BuildContextExtension on BuildContext {
  FuzzystarterLocalizations get fuzzystarterLocalizations => FuzzystarterLocalizations.of(this)!;

  UiColors get uiColors => Theme.of(this).extension<UiColors>()!;

  UiTextStyles get uiTextStyles => Theme.of(this).extension<UiTextStyles>()!;

  UiFormStyles get uiFormStyles => Theme.of(this).extension<UiFormStyles>()!;
}
