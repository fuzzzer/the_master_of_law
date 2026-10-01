import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// One settings row: icon, title, trailing value, optional tap.
class SettingsTile extends StatelessWidget {
  const SettingsTile({
    required this.icon,
    required this.title,
    required this.trailing,
    this.onTap,
    super.key,
  });

  final IconData icon;
  final String title;
  final Widget trailing;
  final VoidCallback? onTap;

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
        onTap: onTap,
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
class ModelSection extends StatelessWidget {
  const ModelSection({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    return BlocBuilder<ModelConfigCubit, ModelConfigState>(
      builder: (context, state) {
        final config = state.config;

        if (state.status == ModelConfigStatus.loading && config == null) {
          return const SettingsTile(
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
          return SettingsTile(
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
