import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryLoadingPageView extends StatelessWidget {
  const PrimaryLoadingPageView({super.key});

  @override
  Widget build(BuildContext context) {
    //Add proper page loader in the future
    return const PrimaryScaffold(
      body: PrimaryLoader(),
      hasAutomaticBackButton: false,
    );
  }
}
