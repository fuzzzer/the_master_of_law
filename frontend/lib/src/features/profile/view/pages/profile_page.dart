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
    return BlocProvider(
      create: (_) => ModelConfigCubit()..load(),
      child: Builder(builder: _buildScaffold),
    );
  }

  Widget _buildScaffold(BuildContext context) {
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
                        isDark ? ChosenBrightness.dark : ChosenBrightness.light,
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
          const _ModelSection(),
          _SettingsTile(
            icon: Icons.info_outline,
            title: 'ვერსია',
            trailing: Text(
              sl.get<PackageInfo>().version,
              style: type.control.copyWith(color: colors.inkMute),
            ),
          ),
          SizedBox(height: space.xl),

          // Legal section. An app that answers legal questions and sends the
          // user's words to a third-party model has to say so somewhere the
          // user can actually reach — these two screens are that somewhere,
          // and `_ToolTile` is reused rather than a new row type invented.
          Text('სამართლებრივი', style: type.titleS.copyWith(color: colors.ink)),
          SizedBox(height: space.m),
          _ToolTile(
            icon: Icons.privacy_tip_outlined,
            title: 'კონფიდენციალურობის პოლიტიკა',
            subtitle: 'რა ინფორმაცია იგზავნება და სად ინახება',
            onTap: () => context.go('/profile/privacy'),
          ),
          SizedBox(height: space.s),
          _ToolTile(
            icon: Icons.description_outlined,
            title: 'მომსახურების პირობები',
            subtitle: 'ეს არ არის იურიდიული კონსულტაცია',
            onTap: () => context.go('/profile/terms'),
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

/// The two model tiers, and a picker for each.
///
/// Lives on the profile screen next to theme and language because it now IS
/// the same kind of thing to the system as well as to the person: under
/// bring-your-own-key the model is paid for by this user's key, out of this
/// user's quota, so choosing one is as personal as choosing a theme.
///
/// It was previously an admin-only global setting, and the read-only path on
/// `can_edit` is kept for deployments that go back to operator-paid AI.
class _ModelSection extends StatelessWidget {
  const _ModelSection();

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    return BlocBuilder<ModelConfigCubit, ModelConfigState>(
      builder: (context, state) {
        final config = state.config;

        if (state.status == ModelConfigStatus.loading && config == null) {
          return const _SettingsTile(
            icon: Icons.memory,
            title: 'AI მოდელები',
            // The kit's own ring: certified size, kit colours, and a QA
            // identifier for free. A hand-rolled SizedBox+CircularProgress
            // here would be two raw dimensions the brand pack cannot reach.
            trailing: FuzzzyProgressRing(qaId: 'models.loading'),
          );
        }

        if (config == null) {
          // The section is additive: if the endpoint is unreachable the rest
          // of the settings screen must still work, so this degrades to one
          // quiet row rather than an error state for the whole page.
          return _SettingsTile(
            icon: Icons.memory,
            title: 'AI მოდელები',
            trailing: Text(
              'მიუწვდომელია',
              style: type.control.copyWith(color: colors.inkFaint),
            ),
          );
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ModelTile(
              tier: 'strong',
              icon: Icons.auto_awesome,
              title: 'ძლიერი მოდელი',
              // Named by what it DOES, not by which pipeline phase it is:
              // "phase 2 generation" means nothing on a settings screen.
              subtitle: 'პასუხის წერა, საქმის ანალიზი',
              value: config.strong,
              available: config.available,
              canEdit: config.canEdit,
              pending: state.pendingTier == 'strong',
              busy: state.isBusy,
            ),
            _ModelTile(
              tier: 'cheap',
              icon: Icons.bolt,
              title: 'სწრაფი მოდელი',
              subtitle: 'ძიება, დახარისხება, გადამოწმება',
              value: config.cheap,
              available: config.available,
              canEdit: config.canEdit,
              pending: state.pendingTier == 'cheap',
              busy: state.isBusy,
            ),
            if (config.strong.isOverride || config.cheap.isOverride)
              Padding(
                padding: EdgeInsets.only(left: space.m, bottom: space.xs),
                child: TextButton(
                  onPressed: state.isBusy || !config.canEdit
                      ? null
                      : () => context.read<ModelConfigCubit>().reset(),
                  child: Text(
                    'ნაგულისხმევზე დაბრუნება',
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                ),
              ),
            if (state.error != null)
              Padding(
                padding: EdgeInsets.only(
                  left: space.m,
                  right: space.m,
                  bottom: space.s,
                ),
                child: Text(
                  state.error!,
                  style: type.bodyS.copyWith(color: colors.destructiveText),
                ),
              ),
          ],
        );
      },
    );
  }
}

class _ModelTile extends StatelessWidget {
  const _ModelTile({
    required this.tier,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.available,
    required this.canEdit,
    required this.pending,
    required this.busy,
  });

  final String tier;
  final IconData icon;
  final String title;
  final String subtitle;
  final TierModel value;
  final List<String> available;
  final bool canEdit;
  final bool pending;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    final enabled = canEdit && !busy && available.isNotEmpty;

    return Padding(
      padding: EdgeInsets.only(bottom: space.xs),
      child: ListTile(
        leading: Icon(icon, color: colors.inkMute),
        title: Text(title, style: type.body.copyWith(color: colors.ink)),
        subtitle: Text(
          subtitle,
          style: type.bodyS.copyWith(color: colors.inkFaint),
        ),
        dense: true,
        enabled: enabled,
        onTap: enabled ? () => _pick(context) : null,
        trailing: pending
            ? FuzzzyProgressRing(qaId: 'models.$tier.pending')
            : ConstrainedBox(
                // A model id is long and Georgian labels are wide; without a
                // ceiling the trailing text pushes the row past the gutter.
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.sizeOf(context).width * 0.42,
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: Text(
                        value.model,
                        textAlign: TextAlign.end,
                        overflow: TextOverflow.ellipsis,
                        style: type.control.copyWith(
                          // An overridden tier is not the deployed default,
                          // and the reader should be able to see that at a
                          // glance rather than by remembering.
                          color: value.isOverride ? colors.ink : colors.inkMute,
                        ),
                      ),
                    ),
                    if (enabled)
                      Icon(Icons.expand_more, color: colors.inkFaint),
                  ],
                ),
              ),
      ),
    );
  }

  Future<void> _pick(BuildContext context) async {
    final cubit = context.read<ModelConfigCubit>();
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final chosen = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(radius.l)),
      ),
      isScrollControlled: true,
      builder: (sheetContext) => SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.sizeOf(sheetContext).height * 0.7,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: density.card,
                child: Text(
                  title,
                  style: type.titleS.copyWith(color: colors.ink),
                ),
              ),
              Flexible(
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: available.length,
                  itemBuilder: (_, i) {
                    final model = available[i];
                    final selected = model == value.model;
                    return ListTile(
                      dense: true,
                      title: Text(
                        model,
                        style: type.body.copyWith(
                          color: selected ? colors.ink : colors.inkMute,
                        ),
                      ),
                      trailing: selected
                          ? Icon(Icons.check, color: colors.ink)
                          : null,
                      onTap: () => Navigator.of(sheetContext).pop(model),
                    );
                  },
                ),
              ),
              SizedBox(height: space.s),
            ],
          ),
        ),
      ),
    );

    if (chosen != null && chosen != value.model) {
      await cubit.select(tier, chosen);
    }
  }
}
