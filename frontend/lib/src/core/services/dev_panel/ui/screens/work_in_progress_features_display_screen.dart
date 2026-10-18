// ignore_for_file: avoid_redundant_argument_values

import 'package:flutter/material.dart';

class WorkInProgressFeaturesDisplayScreen extends StatelessWidget {
  const WorkInProgressFeaturesDisplayScreen({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: SafeArea(
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
