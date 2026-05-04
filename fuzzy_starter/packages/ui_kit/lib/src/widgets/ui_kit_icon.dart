import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class UiKitIcon extends StatelessWidget {
  const UiKitIcon(this.iconPath, {super.key, this.color, this.size}) : height = null, width = null;

  const UiKitIcon.rect(this.iconPath, {super.key, this.color, this.height, this.width}) : size = null;

  final String iconPath;
  final Color? color;
  final double? size;

  final double? width;
  final double? height;

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      iconPath,
      colorFilter: color != null ? ColorFilter.mode(color!, BlendMode.srcIn) : null,
      width: width ?? size,
      height: height ?? size,
      package: 'ui_kit',
    );
  }
}
