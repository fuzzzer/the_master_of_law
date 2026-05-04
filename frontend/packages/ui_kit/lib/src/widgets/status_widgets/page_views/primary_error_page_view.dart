import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryErrorPageView extends StatelessWidget {
  final String message;
  final bool hasAutomaticBackButton;

  const PrimaryErrorPageView({
    super.key,
    required this.message,
    this.hasAutomaticBackButton = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;

    return PrimaryScaffold(
      hasAutomaticBackButton: hasAutomaticBackButton,
      body: Center(
        child: Text(
          message,
          style: uiTextStyles.body16.copyWith(
            color: uiColors.errorColor,
          ),
        ),
      ),
    );
  }
}
