import 'package:flutter/material.dart';

class PrimaryLoader extends StatelessWidget {
  const PrimaryLoader({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: SizedBox.square(
        dimension: 32,
        child: CircularProgressIndicator(),
      ),
    );
  }
}
