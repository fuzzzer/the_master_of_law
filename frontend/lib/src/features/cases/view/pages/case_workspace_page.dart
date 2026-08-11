import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:themasteroflaw/src/src.dart';

/// The core workspace: container with 8 scrollable tabs for a single case.
class CaseWorkspacePage extends StatefulWidget {
  const CaseWorkspacePage({
    super.key,
    required this.caseId,
    this.initialTab = 0,
  });

  final String caseId;
  final int initialTab;

  static void navigate(BuildContext context, String caseId) {
    context.go('/cases/$caseId');
  }

  @override
  State<CaseWorkspacePage> createState() => _CaseWorkspacePageState();
}

class _CaseWorkspacePageState extends State<CaseWorkspacePage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  /// The ten tabs, as (glyph, label) pairs. The fork prefixed a full-colour
  /// emoji into each label STRING, so the strip carried ten unrelated hues and
  /// ten platform-decided glyph metrics that `textScaler` moved independently
  /// of `type.control`. Now a monochrome Material glyph that inherits the
  /// TabBar's own `labelColor`/`unselectedLabelColor`, so the selected state
  /// is still the ONE thing that changes colour. Glyphs deliberately match the
  /// ones M8 chose for the same concepts on the overview dashboard — the tab
  /// and the stat card for "ფაქტები" must not be two different pictures.
  static const _tabs = <(IconData, String)>[
    (Icons.dashboard_outlined, 'მიმოხილვა'),
    (Icons.forum_outlined, 'AI'),
    (Icons.checklist, 'დავალებები'),
    (Icons.fact_check_outlined, 'ფაქტები'),
    (Icons.balance, 'არგუმენტები'),
    (Icons.attach_file, 'მტკიცებ.'),
    (Icons.shield_outlined, 'სტრატეგია'),
    (Icons.timeline, 'ვადები'),
    (Icons.warning_amber_outlined, 'რისკები'),
    (Icons.menu_book_outlined, 'კანონები'),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: _tabs.length,
      vsync: this,
      initialIndex: widget.initialTab,
    );
    context.read<CaseDetailCubit>().loadCase(widget.caseId);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;

    return BlocConsumer<CaseDetailCubit, CaseDetailState>(
      listenWhen: (prev, curr) => !prev.saveFailed && curr.saveFailed,
      listener: (context, state) {
        FuzzzyToast.show(
          context,
          message: 'ცვლილების შენახვა ვერ მოხერხდა',
          kind: FuzzzyToastKind.error,
          qaId: 'caseWorkspace.saveFailed',
        );
      },
      builder: (context, state) {
        final caseData = state.caseData;

        return Scaffold(
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => context.go('/cases'),
            ),
            // Title style and icon colours come from appBarTheme.
            title: caseData != null
                ? Text(
                    caseData.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  )
                : null,
            actions: [
              if (caseData != null)
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert),
                  // Rung 2: a popup is an overlay, so `raised` + `lineStrong`.
                  // `elevation: 0` is SET here rather than deleted —
                  // PopupMenuButton defaults to a Material shadow and Ink's
                  // elevation step is the border (kit-queue item 10's note).
                  color: colors.raised,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(context.fuzzzyRadius.m),
                    side: BorderSide(color: colors.lineStrong),
                  ),
                  onSelected: (value) {
                    switch (value) {
                      case 'review':
                        _reviewCase(caseData);
                      case 'export':
                        _exportCase(caseData);
                      case 'archive':
                        _archiveCase(caseData);
                      case 'delete':
                        _confirmDeleteCase(caseData);
                    }
                  },
                  itemBuilder: (_) => [
                    _menuItem(
                      context,
                      'review',
                      Icons.rate_review_outlined,
                      'შეფასება',
                    ),
                    _menuItem(context, 'export', Icons.share, 'ექსპორტი'),
                    _menuItem(
                      context,
                      'archive',
                      Icons.archive_outlined,
                      'დაარქივება',
                    ),
                    // The screen's ONE red voice besides the tab rail is a
                    // deliberate exception the MAPPING pre-decided: the tab
                    // indicator is `live` (navigational spine) and delete stays
                    // TEXT-only in `destructiveText` — duty 4's idle form, no
                    // fill (MAPPING §2.2 judgement 3).
                    _menuItem(
                      context,
                      'delete',
                      Icons.delete_outline,
                      'წაშლა',
                      destructive: true,
                    ),
                  ],
                ),
            ],
            bottom: caseData != null
                ? PreferredSize(
                    // Dimension: the reserved height of the status row + tab
                    // strip below the title.
                    preferredSize: const Size.fromHeight(80),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Status + domain row
                        Padding(
                          padding: EdgeInsets.symmetric(
                            horizontal: density.screen.left,
                          ),
                          child: Row(
                            children: [
                              _StatusChip(status: caseData.status),
                              SizedBox(width: space.s),
                              _DomainChip(domain: caseData.domain),
                              const Spacer(),
                              Text(
                                '${caseData.completenessPercent}%',
                                // Tabular, Latin-only → the mono `dataS` role.
                                style: type.dataS.copyWith(color: colors.ink),
                              ),
                            ],
                          ),
                        ),
                        SizedBox(height: space.s),
                        // Tab bar
                        TabBar(
                          controller: _tabController,
                          isScrollable: true,
                          tabAlignment: TabAlignment.start,
                          labelColor: colors.ink,
                          unselectedLabelColor: colors.inkMute,
                          // 🔴 USING §6 duty 3: the active marker in a STRIP is
                          // the 2px `live` rail. This is the screen's red
                          // voice, which is why the delete action above stays
                          // outlined text (MAPPING §2.2 judgement 3, decided at
                          // M0 so M7 would not re-litigate it).
                          indicatorColor: colors.live,
                          indicatorSize: TabBarIndicatorSize.label,
                          // Selected and unselected share ONE style: the fork
                          // used labelBold12 vs label12, so moving between tabs
                          // re-measured every label and could re-scroll the
                          // strip. Weight is not a selection signal here — the
                          // colour and the rail are.
                          labelStyle: type.control,
                          unselectedLabelStyle: type.control,
                          dividerColor: colors.line,
                          padding: EdgeInsets.symmetric(horizontal: space.s),
                          // `Tab(child:)` rather than `Tab(icon:, text:)`:
                          // the icon+text form stacks and takes the tab from
                          // 46 to 72px, which would blow the 80px
                          // PreferredSize this AppBar reserves. The Row keeps
                          // the strip's height byte-identical and only grows
                          // it horizontally, where it already scrolls.
                          tabs: _tabs
                              .map(
                                (t) => Tab(
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(t.$1, size: 16),
                                      SizedBox(width: space.xs),
                                      Text(t.$2),
                                    ],
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                      ],
                    ),
                  )
                : null,
          ),
          body: caseData == null
              ? state.status.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : Center(
                        child: Text(
                          'საქმე ვერ მოიძებნა',
                          style: type.body.copyWith(color: colors.inkMute),
                        ),
                      )
              : TabBarView(
                  controller: _tabController,
                  children: [
                    CaseOverviewSection(
                      caseData: caseData,
                      onTabSwitch: _switchToTab,
                    ),
                    CaseChatSection(caseId: widget.caseId),
                    CaseTasksSection(caseData: caseData),
                    CaseFactsSection(caseData: caseData),
                    CaseArgumentsSection(caseData: caseData),
                    CaseEvidenceSection(caseData: caseData),
                    CaseStrategySection(caseData: caseData),
                    CaseTimelineSection(caseData: caseData),
                    CaseRisksSection(caseData: caseData),
                    CaseLawsSection(caseData: caseData),
                  ],
                ),
        );
      },
    );
  }

  /// One shape for all four overflow-menu rows. `body` in `ink`, or
  /// `destructiveText` for the destructive one — no gold "primary" row.
  PopupMenuItem<String> _menuItem(
    BuildContext context,
    String value,
    IconData icon,
    String label, {
    bool destructive = false,
  }) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final fg = destructive ? colors.destructiveText : colors.ink;
    return PopupMenuItem(
      value: value,
      child: Row(
        children: [
          Icon(icon, size: 20, color: fg),
          SizedBox(width: context.fuzzzySpace.s),
          Text(label, style: type.body.copyWith(color: fg)),
        ],
      ),
    );
  }

  void _switchToTab(int index) {
    _tabController.animateTo(index);
  }

  void _reviewCase(CaseData caseData) {
    FeedbackSheet.show(
      context,
      targetId: caseData.id,
      targetType: FeedbackTargetType.caseFile,
    );
  }

  void _exportCase(CaseData caseData) {
    CaseExportHelper.exportToClipboard(context, caseData);
  }

  void _archiveCase(CaseData caseData) {
    context.read<CaseDetailCubit>().updateStatus(CaseStatus.closed);
  }

  void _confirmDeleteCase(CaseData caseData) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) {
        final colors = dialogContext.fuzzzyColors;
        final type = dialogContext.fuzzzyTextStyles;
        final radius = dialogContext.fuzzzyRadius;
        return AlertDialog(
          // Overlay rung: `raised` + `lineStrong`.
          backgroundColor: colors.raised,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius.l),
            side: BorderSide(color: colors.lineStrong),
          ),
          title: Text(
            'საქმის წაშლა',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          content: Text(
            'ნამდვილად გსურთ „${caseData.title}" საქმის წაშლა?',
            style: type.body.copyWith(color: colors.inkMute),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              // `FuzzzyButton.ghost` idle foreground.
              child: Text(
                'გაუქმება',
                style: type.control.copyWith(color: colors.inkMute),
              ),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext);
                context.read<CasesCubit>().deleteCase(caseData.id);
                context.go('/cases');
              },
              // This IS the destructive commit (USING §6 duty 4's "confirm"),
              // so it is allowed a fill — but the surrounding dialog already
              // names the action, so it stays the legible `destructiveText` on
              // the overlay rather than shouting a red block at the user.
              child: Text(
                'წაშლა',
                style: type.control.copyWith(color: colors.destructiveText),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// `FuzzzyStatusChip`'s recipe, app-side — see the twin in `case_card.dart` and
/// `PHASE_M_KIT_QUEUE` item 11 for why the kit's own widget cannot take a
/// Georgian label yet.
class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final CaseStatus status;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    final role = switch (status) {
      CaseStatus.active => colors.success,
      CaseStatus.pending => colors.warning,
      CaseStatus.closed => colors.inkMute,
    };

    return Container(
      padding: context.fuzzzyDensity.chip,
      decoration: BoxDecoration(
        border: Border.all(color: Color.lerp(colors.ground, role, 0.40)!),
        borderRadius: BorderRadius.circular(radius.s),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: role,
              borderRadius: BorderRadius.circular(radius.circle),
            ),
          ),
          SizedBox(width: space.s),
          Text(status.displayNameKa, style: type.control.copyWith(color: role)),
        ],
      ),
    );
  }
}

/// `FuzzzyFilterChip`'s neutral `dotColor` variant. Sits on the AppBar's
/// `ground` chrome, so its resting fill is `surface` — the opposite rung from
/// the twin inside `CaseCard`, which sits on a `surface` card.
class _DomainChip extends StatelessWidget {
  const _DomainChip({required this.domain});

  final LegalDomain domain;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return Container(
      padding: context.fuzzzyDensity.chip,
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border.all(color: colors.line),
        borderRadius: BorderRadius.circular(radius.s),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            // The taxonomy disc replaces the fork's '⚖️ ' emoji prefix (which
            // also carried a hardcoded fontSize: 12) — the dot is what the
            // emoji was standing in for, and it actually names the domain.
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: context.legalDomainColors.of(domain),
              borderRadius: BorderRadius.circular(radius.circle),
            ),
          ),
          SizedBox(width: space.s),
          Text(
            domain.shortLabelKa,
            style: type.control.copyWith(color: colors.inkMute),
          ),
        ],
      ),
    );
  }
}
