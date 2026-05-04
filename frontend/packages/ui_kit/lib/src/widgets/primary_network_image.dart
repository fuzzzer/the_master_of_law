import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryNetworkImage extends StatelessWidget {
  const PrimaryNetworkImage({
    super.key,
    required this.imageUrl,
    this.width,
    this.height,
    this.fit,
    this.onError,
  });

  final String imageUrl;
  final double? width;
  final double? height;
  final BoxFit? fit;
  final void Function(Object error)? onError;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return SizedBox(
      width: width,
      height: height,
      child: CachedNetworkImage(
        imageUrl: imageUrl,
        fit: fit ?? BoxFit.cover,
        placeholder: (context, url) => Container(
          color: UiKitColors.backgroundSecondaryColor,
          child: Shimmer.fromColors(
            baseColor: UiKitColors.backgroundPrimaryColor,
            highlightColor: UiKitColors.backgroundSecondaryColor,
            child: Container(
              width: width,
              height: height,
              color: uiColors.primaryColor.withValues(
                alpha: 0.5,
              ),
            ),
          ),
        ),
        errorWidget: (context, url, error) {
          if (onError != null) {
            onError!(error);
          }
          return Container(
            color: uiColors.focusColor,
            child: Center(
              child: Icon(
                Icons.broken_image,
                color: uiColors.primaryColor,
                size: height ?? 50,
              ),
            ),
          );
        },
      ),
    );
  }
}
