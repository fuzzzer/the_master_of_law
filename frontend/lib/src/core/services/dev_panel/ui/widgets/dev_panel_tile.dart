import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;

    // Card surface, border, radius and elevation all come from the app's
    // cardTheme, which is built from kit roles — nothing restated here.
    return Card(
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
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
            style: type.titleS.copyWith(color: colors.ink),
          ),
          subtitle: subtitle != null
              ? Text(
                  subtitle!,
                  style: type.body.copyWith(color: colors.inkMute),
                )
              : null,
          trailing: trailingIcon,
        ),
      ),
    );
  }
}
