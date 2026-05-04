// ignore_for_file: avoid_redundant_argument_values

import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class WorkInProgressFeaturesDisplayScreen extends StatelessWidget {
  const WorkInProgressFeaturesDisplayScreen({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return Scaffold(
      backgroundColor: uiColors.backgroundPrimaryColor,
      body: const SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 32,
          ),
          child: Stack(
            children: [
              Center(
                child: Text('WIP Features are empty'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
