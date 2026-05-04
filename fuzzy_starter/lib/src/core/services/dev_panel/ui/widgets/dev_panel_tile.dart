import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class DevPanelTile extends StatelessWidget {
  const DevPanelTile({
    super.key,
    this.leadingIcon,
    required this.title,
    this.subtitle,
    this.trailingIcon,
    this.onTap,
  });

  final Widget? leadingIcon;
  final String title;
  final String? subtitle;
  final Widget? trailingIcon;
  final void Function()? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return Card(
      elevation: 0,
      color: uiColors.backgroundSecondaryColor,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 10,
          ),
          leading: Container(
            padding: const EdgeInsets.only(right: 12),
            margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            child: leadingIcon ?? const SizedBox.shrink(),
          ),
          title: Text(
            title,
            style: TextStyle(
              color: uiColors.backgroundPrimaryColor,
              fontWeight: FontWeight.bold,
            ),
          ),
          subtitle: subtitle != null
              ? Text(
                  subtitle!,
                  style: TextStyle(
                    color: uiColors.backgroundPrimaryColor,
                  ),
                )
              : null,
          trailing: trailingIcon,
        ),
      ),
    );
  }
}
