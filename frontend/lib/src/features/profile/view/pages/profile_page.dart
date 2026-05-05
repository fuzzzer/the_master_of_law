import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// User profile page with settings, legal tools, and credits.
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'პროფილი',
          style: uiTextStyles.headlineBold20.copyWith(color: uiColors.accentColor),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // User card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: uiColors.backgroundSecondaryColor,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 32,
                  backgroundColor: uiColors.accentColor.withValues(alpha: 0.2),
                  child: Icon(Icons.person, size: 32, color: uiColors.accentColor),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'მომხმარებელი',
                        style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: uiColors.accentColor.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '50 კრედიტი',
                          style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Legal tools section
          Text(
            'იურიდიული ხელსაწყოები',
            style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 12),
          _ToolTile(
            icon: Icons.menu_book,
            title: 'იურიდიული ლექსიკონი',
            subtitle: '500+ ტერმინი ქართულად',
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
            onTap: () {},
          ),
          const SizedBox(height: 8),
          _ToolTile(
            icon: Icons.gavel,
            title: 'სასამართლო ეტიკეტი',
            subtitle: 'როგორ მოვიქცეთ სასამართლოში',
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
            onTap: () {},
          ),
          const SizedBox(height: 8),
          _ToolTile(
            icon: Icons.contact_phone,
            title: 'სასარგებლო კონტაქტები',
            subtitle: 'იურისტები, ჰოთლაინი, ორგანიზაციები',
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
            onTap: () {},
          ),
          const SizedBox(height: 20),

          // Settings section
          Text(
            'პარამეტრები',
            style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 12),
          _SettingsTile(
            icon: Icons.dark_mode,
            title: 'თემა',
            trailing: BlocBuilder<ThemeCubit, ThemeState>(
              builder: (context, state) {
                return Switch(
                  value: state.chosenBrightness.isDark,
                  activeColor: uiColors.accentColor,
                  onChanged: (isDark) => context.read<ThemeCubit>().setBrightness(
                        isDark ? ChosenBrightness.dark : ChosenBrightness.light,
                      ),
                );
              },
            ),
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
          ),
          _SettingsTile(
            icon: Icons.language,
            title: 'ენა',
            trailing: Text('ქართული', style: uiTextStyles.label14.copyWith(color: uiColors.secondaryTextColor)),
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
          ),
          _SettingsTile(
            icon: Icons.info_outline,
            title: 'ვერსია',
            trailing: Text('0.1.0', style: uiTextStyles.label14.copyWith(color: uiColors.secondaryTextColor)),
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
          ),
        ],
      ),
    );
  }
}

class _ToolTile extends StatelessWidget {
  const _ToolTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: uiColors.accentColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: uiColors.accentColor, size: 24),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
                  Text(subtitle, style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: uiColors.secondaryTextColor),
          ],
        ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.trailing,
    required this.uiColors,
    required this.uiTextStyles,
  });

  final IconData icon;
  final String title;
  final Widget trailing;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: ListTile(
        leading: Icon(icon, color: uiColors.secondaryTextColor),
        title: Text(title, style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
        trailing: trailing,
        dense: true,
      ),
    );
  }
}
