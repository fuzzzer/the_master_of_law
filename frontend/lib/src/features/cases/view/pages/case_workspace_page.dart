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
        // Built once, used twice: mounted in the header Column below, and
        // MEASURED by `_headerHeight`. Two instances would be two chances to
        // drift, which is the same failure `_DomainChip` was consolidated for.
        final tabBar = caseData == null ? null : _tabBar(context);

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
                    // 🔴 DERIVED, not the hardcoded `Size.fromHeight(80)` this
                    // used to be (`T-0263`). Three things were wrong with the
                    // literal: it is a raw dimension where roles belong; it did
                    // not move with `textScaler`, so at 1.3 the reserve was
                    // ~16 px short of what the chip row needs; and it did not
                    // move with the **pack** — the stress pack's `density.chip`
                    // is 12 px vertical against ink's 6, which alone puts the
                    // row over an 80 px budget. See [_headerHeight].
                    preferredSize: Size.fromHeight(_headerHeight(context, tabBar!)),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Status + domain row
                        Padding(
                          padding: EdgeInsets.symmetric(
                            horizontal: density.screen.left,
                          ),
                          // 🔴 M14b filed the overflow here (two unbounded
                          // chips plus a `%` readout, 39 px right under the
                          // stress pack, on all ten tabs) and made both chips
                          // `Flexible`. That stopped the overflow and created
                          // `T-0263`: on the SHIPPED ink build at 1.3/360 both
                          // labels truncated to `აქტ…` and `სისხ…`.
                          //
                          // The cause was NOT the height, and not a genuine
                          // shortage of width — it was the `Spacer` that used
                          // to sit between the chips and the `%`. **A `Spacer`
                          // is a flex child** (`Expanded(child: SizedBox())`),
                          // so `RenderFlex` split the free space three ways and
                          // capped each chip at a THIRD of the row while a
                          // third of it stayed visibly empty. Measured at
                          // 1.3/360 (M17): 50.2 px of label budget per chip
                          // with the `Spacer`, **90.8 px without** — same
                          // widths, same fonts, same everything else.
                          //
                          // This is the exact trap M14d already recorded for
                          // `case_arguments_section` ("Spacer had to GO, not
                          // stay") and then did not apply here. The trailing
                          // gap is now `mainAxisAlignment.spaceBetween`, which
                          // distributes what the loose `Flexible` child did
                          // *not* take — so the chips get the whole row to
                          // grow into and the `%` still sits hard right.
                          //
                          // Wrapping to a second run was considered and
                          // rejected: a `Wrap` under a `PreferredSize` whose
                          // height must be known before layout would trade a
                          // horizontal ellipsis for a vertical overflow, which
                          // is the same bad trade M14b made once already.
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Flexible(
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Flexible(
                                      child: AppStatusChip(
                                        label: caseData.status.displayNameKa,
                                        kind: caseStatusKind(caseData.status),
                                        qaId: 'workspaceStatus',
                                      ),
                                    ),
                                    SizedBox(width: space.s),
                                    Flexible(
                                      child: AppDomainChip(
                                        domain: caseData.domain,
                                        // On the AppBar's `ground` chrome →
                                        // a `surface` box.
                                        parent: AppChipParent.ground,
                                        qaId: 'workspaceDomain',
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              SizedBox(width: space.s),
                              Text(
                                '${caseData.completenessPercent}%',
                                // Tabular, Latin-only → the mono `dataS` role.
                                style: type.dataS.copyWith(color: colors.ink),
                              ),
                            ],
                          ),
                        ),
                        SizedBox(height: space.s),
                        // Tab bar. Built ONCE into `tabBar` above so that
                        // `_headerHeight` measures the very widget that is in
                        // the tree — see its doc for why asking the widget
                        // beats restating 46 + 2 in a second place.
                        tabBar,
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

  /// The height [PreferredSize] must reserve: one chip row + `space.s` + the
  /// tab strip.
  ///
  /// Replaces a hardcoded `80`. That literal was wrong along **two** axes it
  /// could not see:
  ///
  /// - **`textScaler`.** The chip row is type plus padding, so it grows with
  ///   the user's text size. At 1.3 the row alone wants ~38 px against the ~26
  ///   the literal implicitly budgeted.
  /// - **the pack.** `density.chip` is 6 px vertical in ink and **12** in the
  ///   stress pack, and `space.s` moves too — so the one number could not be
  ///   right for both, and `USING.md` §10's whole point is that a screen must
  ///   survive a pack swap.
  ///
  /// The tab strip is not restated here: [TabBar] implements
  /// `PreferredSizeWidget`, so it is asked. That is what keeps this correct if
  /// someone ever gives a `Tab` an `icon:` (which stacks it from 46 px to 72
  /// and is exactly the change the tab-strip comment warns about) — the
  /// reserve follows instead of silently clipping.
  double _headerHeight(BuildContext context, TabBar tabBar) {
    final type = context.fuzzzyTextStyles;
    final density = context.fuzzzyDensity;

    // One chip: the label's real line box, the pack's chip padding, and the
    // 1 px border on each side.
    //
    // 🔴 The line box is MEASURED, not computed. `fontSize * height * scaler`
    // is the obvious formula and it is wrong — it returned 34.25 px against a
    // chip that actually renders 24.8 px at scale 1.0 and 29.8 at 1.3 (both
    // measured at M17). Font metrics are not `fontSize × height`, and guessing
    // them is how the literal 80 came to be off in the first place. A
    // `TextPainter` on the same style the chips use is the same layout the
    // framework will perform, so it cannot drift from them.
    final probe = TextPainter(
      // Any single Mkhedruli glyph: line height is a property of the FONT and
      // the style, not of the string. Using a real Georgian glyph rather than
      // 'x' keeps it honest if a fallback face ever changes the metrics.
      text: TextSpan(text: 'ა', style: type.control),
      textDirection: Directionality.of(context),
      textScaler: MediaQuery.textScalerOf(context),
      maxLines: 1,
    )..layout();
    final chipRow = probe.height + density.chip.vertical + 2;

    return chipRow + context.fuzzzySpace.s + tabBar.preferredSize.height;
  }

  /// The tab strip, built as a value so [_headerHeight] can measure the
  /// instance that is actually mounted.
  TabBar _tabBar(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    return TabBar(
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
                          // 46 to 72px. That used to blow the AppBar's hard
                          // 80px reserve; since M17 `_headerHeight` measures
                          // this widget instead, so the consequence would be a
                          // taller header rather than a clipped one — but the
                          // Row is still the right shape, because it grows the
                          // strip only horizontally, where it already scrolls.
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

