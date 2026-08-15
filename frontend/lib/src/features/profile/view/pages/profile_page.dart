import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// User profile page with settings, legal tools, and credits.
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Scaffold(
      // Title style comes from appBarTheme (titleM + ink), built from roles.
      appBar: AppBar(title: const Text('პროფილი')),
      body: ListView(
        padding: density.screen,
        children: [
          // User card — rung 1 of the ladder: surface + line + radius.l.
          Container(
            padding: density.card,
            decoration: BoxDecoration(
              color: colors.surface,
              border: Border.all(color: colors.line),
              borderRadius: BorderRadius.circular(radius.l),
            ),
            child: Row(
              children: [
                // The disc sits ON a surface card, so it takes the recessed
                // `ground` well rather than `surface` (which would vanish).
                CircleAvatar(
                  radius: 32,
                  backgroundColor: colors.ground,
                  child: Icon(Icons.person, size: 32, color: colors.ink),
                ),
                SizedBox(width: space.l),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'მომხმარებელი',
                        style: type.titleS.copyWith(color: colors.ink),
                      ),
                      SizedBox(height: space.xs),
                      BlocBuilder<CreditsCubit, CreditsState>(
                        builder: (context, creditsState) {
                          final String label;
                          if (creditsState.status.isLoading &&
                              !creditsState.hasBalance) {
                            label = '...';
                          } else if (creditsState.hasBalance) {
                            label = '${creditsState.balance} კრედიტი';
                          } else {
                            label = 'კრედიტები მიუწვდომელია';
                          }
                          return GestureDetector(
                            behavior: HitTestBehavior.opaque,
                            onTap: () => context.read<CreditsCubit>().load(),
                            child: Container(
                              padding: density.chip,
                              decoration: BoxDecoration(
                                color: colors.ground,
                                border: Border.all(color: colors.line),
                                borderRadius: BorderRadius.circular(radius.s),
                              ),
                              child: Text(
                                label,
                                style: type.control.copyWith(color: colors.ink),
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: space.xl),

          // Legal tools section
          Text(
            'იურიდიული ხელსაწყოები',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.m),
          _ToolTile(
            icon: Icons.menu_book,
            title: 'იურიდიული ლექსიკონი',
            subtitle: '500+ ტერმინი ქართულად',
            onTap: () => context.go('/profile/dictionary'),
          ),
          SizedBox(height: space.s),
          _ToolTile(
            icon: Icons.gavel,
            title: 'სასამართლო ეტიკეტი',
            subtitle: 'როგორ მოვიქცეთ სასამართლოში',
            onTap: () => context.go('/profile/etiquette'),
          ),
          SizedBox(height: space.s),
          _ToolTile(
            icon: Icons.contact_phone,
            title: 'სასარგებლო კონტაქტები',
            subtitle: 'იურისტები, ჰოთლაინი, ორგანიზაციები',
            onTap: () => context.go('/profile/contacts'),
          ),
          SizedBox(height: space.xl),

          // Settings section
          Text('პარამეტრები', style: type.titleS.copyWith(color: colors.ink)),
          SizedBox(height: space.m),
          _SettingsTile(
            icon: Icons.dark_mode,
            title: 'თემა',
            trailing: BlocBuilder<ThemeCubit, ThemeState>(
              builder: (context, state) {
                return Switch(
                  value: state.chosenBrightness.isDark,
                  activeColor: colors.actionPrimaryBg,
                  onChanged: (isDark) =>
                      context.read<ThemeCubit>().setBrightness(
                            isDark
                                ? ChosenBrightness.dark
                                : ChosenBrightness.light,
                          ),
                );
              },
            ),
          ),
          _SettingsTile(
            icon: Icons.language,
            title: 'ენა',
            trailing: Text(
              'ქართული',
              style: type.control.copyWith(color: colors.inkMute),
            ),
          ),
          _SettingsTile(
            icon: Icons.info_outline,
            title: 'ვერსია',
            trailing: Text(
              sl.get<PackageInfo>().version,
              style: type.control.copyWith(color: colors.inkMute),
            ),
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
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: density.panel,
        decoration: BoxDecoration(
          color: colors.surface,
          border: Border.all(color: colors.line),
          borderRadius: BorderRadius.circular(radius.l),
        ),
        child: Row(
          children: [
            SizedBox(
              // Dimension, not a gap: the certified ≥44×44 target footprint.
              width: FuzzzyViewport.minTouchTarget,
              height: FuzzzyViewport.minTouchTarget,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  // Recessed well on a surface card — see the CircleAvatar
                  // above; `surface` here would be invisible.
                  color: colors.ground,
                  borderRadius: BorderRadius.circular(radius.m),
                ),
                child: Icon(icon, color: colors.ink, size: 24),
              ),
            ),
            SizedBox(width: space.m),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: type.titleS.copyWith(color: colors.ink)),
                  Text(
                    subtitle,
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: colors.inkMute),
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
  });

  final IconData icon;
  final String title;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    return Padding(
      padding: EdgeInsets.only(bottom: space.xs),
      child: ListTile(
        leading: Icon(icon, color: colors.inkMute),
        title: Text(title, style: type.body.copyWith(color: colors.ink)),
        trailing: trailing,
        dense: true,
      ),
    );
  }
}
