import 'package:flutter/material.dart';

class UiKitAssetImage extends StatelessWidget {
  const UiKitAssetImage({
    super.key,
    required this.imagePath,
    this.fit = BoxFit.cover,
    this.width,
    this.height,
    this.color,
  });

  final String imagePath;
  final BoxFit fit;
  final double? width;
  final double? height;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      imagePath,
      fit: fit,
      width: width,
      height: height,
      package: 'ui_kit',
    );
  }
}
