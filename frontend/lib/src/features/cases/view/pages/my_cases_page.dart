import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shimmer/shimmer.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Home screen: List of all user's cases.
/// Empty state with CTA when no cases exist.
class MyCasesPage extends StatefulWidget {
  const MyCasesPage({super.key});

  @override
  State<MyCasesPage> createState() => _MyCasesPageState();
}

class _MyCasesPageState extends State<MyCasesPage> {
  @override
  void initState() {
    super.initState();
    context.read<CasesCubit>().loadCases();
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'კანონის ოსტატი',
          style: uiTextStyles.headlineBold20.copyWith(
            color: uiColors.accentColor,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.search, color: uiColors.secondaryTextColor),
            onPressed: () {
              // TODO: Search cases
            },
          ),
        ],
      ),
      body: BlocBuilder<CasesCubit, CasesState>(
        builder: (context, state) {
          return switch (state.status) {
            StateStatus.initial || StateStatus.loading => _buildShimmer(uiColors),
            StateStatus.failed => _buildError(uiColors, uiTextStyles),
            StateStatus.success => state.cases.isEmpty
                ? _buildEmptyState(uiColors, uiTextStyles)
                : _buildCaseList(state.cases, uiColors, uiTextStyles),
          };
        },
      ),
      floatingActionButton: BlocBuilder<CasesCubit, CasesState>(
        builder: (context, state) {
          if (state.cases.isEmpty) return const SizedBox.shrink();
          return FloatingActionButton(
            onPressed: () => _showNewCaseSheet(context),
            backgroundColor: uiColors.accentColor,
            child: Icon(Icons.add, color: uiColors.backgroundPrimaryColor),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(UiColors uiColors, UiTextStyles uiTextStyles) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.balance,
              size: 72,
              color: uiColors.accentColor.withValues(alpha: 0.6),
            ),
            const SizedBox(height: 24),
            Text(
              'თქვენ ჯერ არ გაქვთ საქმე',
              style: uiTextStyles.headlineBold20.copyWith(
                color: uiColors.primaryTextColor,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'შექმენით პირველი საქმე და\nAI დაგეხმარებათ მის მოწყობაში',
              style: uiTextStyles.body14.copyWith(
                color: uiColors.secondaryTextColor,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                onPressed: () => _showNewCaseSheet(context),
                icon: const Icon(Icons.add),
                label: const Text('ახალი საქმის შექმნა'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: uiColors.accentColor,
                  foregroundColor: uiColors.backgroundPrimaryColor,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  textStyle: uiTextStyles.bodyBold16,
                ),
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () {
                // Navigate to Laws tab
              },
              child: Text(
                'ან შეისწავლეთ კანონები →',
                style: uiTextStyles.body14.copyWith(
                  color: uiColors.accentColor,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCaseList(List<CaseData> cases, UiColors uiColors, UiTextStyles uiTextStyles) {
    return RefreshIndicator(
      onRefresh: () => context.read<CasesCubit>().loadCases(),
      color: uiColors.accentColor,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
        itemCount: cases.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          return CaseCard(
            caseData: cases[index],
            onTap: () => _navigateToCase(cases[index]),
            onDismissed: () => _deleteCase(cases[index].id),
          );
        },
      ),
    );
  }

  Widget _buildShimmer(UiColors uiColors) {
    return Shimmer.fromColors(
      baseColor: uiColors.backgroundSecondaryColor,
      highlightColor: uiColors.surfaceColor,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: 5,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (_, __) => Container(
          height: 100,
          decoration: BoxDecoration(
            color: uiColors.backgroundSecondaryColor,
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  Widget _buildError(UiColors uiColors, UiTextStyles uiTextStyles) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: uiColors.errorColor),
          const SizedBox(height: 16),
          Text(
            'შეცდომა მოხდა',
            style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => context.read<CasesCubit>().loadCases(),
            child: Text(
              'ხელახლა ცდა',
              style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor),
            ),
          ),
        ],
      ),
    );
  }

  void _showNewCaseSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.uiColors.backgroundSecondaryColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => BlocProvider.value(
        value: context.read<CasesCubit>(),
        child: const NewCaseSheet(),
      ),
    );
  }

  void _navigateToCase(CaseData caseData) {
    CaseWorkspacePage.navigate(context, caseData.id);
  }

  Future<void> _deleteCase(String id) async {
    await context.read<CasesCubit>().deleteCase(id);
  }
}
