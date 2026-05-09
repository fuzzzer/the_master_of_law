import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

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

class _CaseWorkspacePageState extends State<CaseWorkspacePage> with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  static const _tabLabels = [
    '📊 მიმოხილვა',
    '💬 AI',
    '✅ დავალებები',
    '📋 ფაქტები',
    '⚖️ არგუმენტები',
    '📎 მტკიცებ.',
    '🛡️ სტრატეგია',
    '📅 ვადები',
    '⚠️ რისკები',
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: _tabLabels.length,
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

  Color _domainColor(LegalDomain domain, UiColors uiColors) => switch (domain) {
        LegalDomain.criminal => uiColors.criminalColor,
        LegalDomain.civil => uiColors.civilColor,
        LegalDomain.administrative => uiColors.administrativeColor,
        LegalDomain.labor => uiColors.laborColor,
        LegalDomain.tax => uiColors.taxColor,
        LegalDomain.family => uiColors.familyColor,
        LegalDomain.property => uiColors.propertyColor,
        LegalDomain.other => uiColors.otherDomainColor,
      };

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return BlocBuilder<CaseDetailCubit, CaseDetailState>(
      builder: (context, state) {
        final caseData = state.caseData;

        return Scaffold(
          appBar: AppBar(
            leading: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () => context.go('/cases'),
            ),
            title: caseData != null
                ? Text(
                    caseData.title,
                    style: uiTextStyles.bodyBold16.copyWith(
                      color: uiColors.primaryTextColor,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  )
                : null,
            actions: [
              if (caseData != null)
                PopupMenuButton<String>(
                  icon: Icon(Icons.more_vert, color: uiColors.secondaryTextColor),
                  color: uiColors.backgroundSecondaryColor,
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
                    PopupMenuItem(
                      value: 'review',
                      child: Row(
                        children: [
                          Icon(Icons.rate_review_outlined, size: 20, color: uiColors.accentColor),
                          const SizedBox(width: 8),
                          Text('შეფასება', style: uiTextStyles.body14.copyWith(color: uiColors.accentColor)),
                        ],
                      ),
                    ),
                    PopupMenuItem(
                      value: 'export',
                      child: Row(
                        children: [
                          Icon(Icons.share, size: 20, color: uiColors.primaryTextColor),
                          const SizedBox(width: 8),
                          Text('ექსპორტი', style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
                        ],
                      ),
                    ),
                    PopupMenuItem(
                      value: 'archive',
                      child: Row(
                        children: [
                          Icon(Icons.archive_outlined, size: 20, color: uiColors.primaryTextColor),
                          const SizedBox(width: 8),
                          Text('დაარქივება', style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
                        ],
                      ),
                    ),
                    PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete_outline, size: 20, color: uiColors.errorColor),
                          const SizedBox(width: 8),
                          Text('წაშლა', style: uiTextStyles.body14.copyWith(color: uiColors.errorColor)),
                        ],
                      ),
                    ),
                  ],
                ),
            ],
            bottom: caseData != null
                ? PreferredSize(
                    preferredSize: const Size.fromHeight(80),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Status + domain row
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Row(
                            children: [
                              _StatusChip(status: caseData.status, uiColors: uiColors, uiTextStyles: uiTextStyles),
                              const SizedBox(width: 8),
                              _DomainChip(domain: caseData.domain, color: _domainColor(caseData.domain, uiColors), uiTextStyles: uiTextStyles),
                              const Spacer(),
                              Text(
                                '${caseData.completenessPercent}%',
                                style: uiTextStyles.labelBold14.copyWith(
                                  color: uiColors.accentColor,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 8),
                        // Tab bar
                        TabBar(
                          controller: _tabController,
                          isScrollable: true,
                          tabAlignment: TabAlignment.start,
                          labelColor: uiColors.accentColor,
                          unselectedLabelColor: uiColors.secondaryTextColor,
                          indicatorColor: uiColors.accentColor,
                          indicatorSize: TabBarIndicatorSize.label,
                          labelStyle: uiTextStyles.labelBold12,
                          unselectedLabelStyle: uiTextStyles.label12,
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          tabs: _tabLabels.map((label) => Tab(text: label)).toList(),
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
                        style: uiTextStyles.body16.copyWith(color: uiColors.secondaryTextColor),
                      ),
                    )
              : TabBarView(
                  controller: _tabController,
                  children: [
                    CaseOverviewSection(caseData: caseData, onTabSwitch: _switchToTab),
                    CaseChatSection(caseId: widget.caseId),
                    CaseTasksSection(caseData: caseData),
                    CaseFactsSection(caseData: caseData),
                    CaseArgumentsSection(caseData: caseData),
                    CaseEvidenceSection(caseData: caseData),
                    CaseStrategySection(caseData: caseData),
                    CaseTimelineSection(caseData: caseData),
                    CaseRisksSection(caseData: caseData),
                  ],
                ),
        );
      },
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
        final uiColors = dialogContext.uiColors;
        final uiTextStyles = dialogContext.uiTextStyles;
        return AlertDialog(
          backgroundColor: uiColors.backgroundSecondaryColor,
          title: Text('საქმის წაშლა', style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
          content: Text(
            'ნამდვილად გსურთ „${caseData.title}" საქმის წაშლა?',
            style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: Text('გაუქმება', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext);
                context.read<CasesCubit>().deleteCase(caseData.id);
                context.go('/cases');
              },
              child: Text('წაშლა', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.errorColor)),
            ),
          ],
        );
      },
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status, required this.uiColors, required this.uiTextStyles});
  final CaseStatus status;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      CaseStatus.active => uiColors.successColor,
      CaseStatus.pending => uiColors.warningColor,
      CaseStatus.closed => uiColors.secondaryTextColor,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(status.displayNameKa, style: uiTextStyles.labelBold12.copyWith(color: color)),
    );
  }
}

class _DomainChip extends StatelessWidget {
  const _DomainChip({required this.domain, required this.color, required this.uiTextStyles});
  final LegalDomain domain;
  final Color color;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('⚖️ ', style: TextStyle(fontSize: 12)),
          Text(domain.shortLabelKa, style: uiTextStyles.labelBold12.copyWith(color: color)),
        ],
      ),
    );
  }
}
