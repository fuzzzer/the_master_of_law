import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:shimmer/shimmer.dart';

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
    final colors = context.fuzzzyColors;
    final radius = context.fuzzzyRadius;

    return Scaffold(
      appBar: AppBar(
        // The app's own name was the ONE place the gold accent painted a
        // title. Ink has no decorative-accent text role: emphasis is weight
        // and size, and the colour stays `ink` (MAPPING §2.2 judgement 1).
        // Style + colour now come from appBarTheme.
        title: const Text('ბუნდოვანი კანონი'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // TODO: Search cases
            },
          ),
        ],
      ),
      body: BlocBuilder<CasesCubit, CasesState>(
        builder: (context, state) {
          return switch (state.status) {
            StateStatus.initial || StateStatus.loading => _buildShimmer(context),
            StateStatus.failed => _buildError(context),
            StateStatus.success =>
              state.cases.isEmpty ? _buildEmptyState(context) : _buildCaseList(context, state.cases),
          };
        },
      ),
      floatingActionButton: BlocBuilder<CasesCubit, CasesState>(
        builder: (context, state) {
          if (state.cases.isEmpty) return const SizedBox.shrink();
          return FloatingActionButton(
            onPressed: () => _showNewCaseSheet(context),
            backgroundColor: colors.actionPrimaryBg,
            foregroundColor: colors.actionPrimaryFg,
            // Material 3's default FAB is a 16px-rounded square with a shadow.
            // Ink has no shadow vocabulary and its radii collapse to 2/3/4, so
            // a disc is the honest shape — the same one the consultation
            // composer's send button uses.
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(radius.circle),
            ),
            elevation: 0,
            child: const Icon(Icons.add),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return Center(
      child: Padding(
        // A centred state panel's inset is a footprint, not a gap (USING §4.3).
        padding: density.screen,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Oversized decorative state glyph → `inkFaint`, alpha deleted.
            Icon(Icons.balance, size: 72, color: colors.inkFaint),
            SizedBox(height: space.xl),
            Text(
              'თქვენ ჯერ არ გაქვთ საქმე',
              style: type.titleM.copyWith(color: colors.ink),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.m),
            Text(
              'შექმენით პირველი საქმე და\nAI დაგეხმარებათ მის მოწყობაში',
              style: type.body.copyWith(color: colors.inkMute),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xxl),
            SizedBox(
              width: double.infinity,
              // Dimension: the full-width primary CTA's fixed height.
              height: 52,
              child: ElevatedButton.icon(
                onPressed: () => _showNewCaseSheet(context),
                icon: const Icon(Icons.add),
                label: const Text('ახალი საქმის შექმნა'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.actionPrimaryBg,
                  foregroundColor: colors.actionPrimaryFg,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                  // A button label is `control`, always — the fork's
                  // `bodyBold16` was body copy doing a control's job.
                  textStyle: type.control,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCaseList(BuildContext context, List<CaseData> cases) {
    final colors = context.fuzzzyColors;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;
    return RefreshIndicator(
      onRefresh: () => context.read<CasesCubit>().loadCases(),
      color: colors.ink,
      backgroundColor: colors.surface,
      child: ListView.separated(
        // Dimension in the last slot: 100 clears the FAB so the final card is
        // never trapped under it.
        padding: density.screen.copyWith(bottom: 100),
        itemCount: cases.length,
        separatorBuilder: (_, __) => SizedBox(height: space.m),
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

  Widget _buildShimmer(BuildContext context) {
    final colors = context.fuzzzyColors;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return Shimmer.fromColors(
      // The skeleton is the surface ladder's two adjacent rungs: the resting
      // panel and the half-step above it. `surfaceColor → raised` per
      // MAPPING §2.7. `FuzzzySkeleton` at M11.
      baseColor: colors.surface,
      highlightColor: colors.raised,
      child: ListView.separated(
        padding: density.screen,
        itemCount: 5,
        separatorBuilder: (_, __) => SizedBox(height: space.m),
        itemBuilder: (_, __) => Container(
          // Dimension: the placeholder card's height, matched to CaseCard's.
          height: 100,
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(radius.l),
          ),
        ),
      ),
    );
  }

  Widget _buildError(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // The 48px glyph is decoration; the copy under it is the error voice
          // (USING §6, one red voice per screen).
          Icon(Icons.error_outline, size: 48, color: colors.inkFaint),
          SizedBox(height: space.l),
          Text('შეცდომა მოხდა', style: type.titleS.copyWith(color: colors.ink)),
          SizedBox(height: space.s),
          TextButton(
            onPressed: () => context.read<CasesCubit>().loadCases(),
            child: Text(
              'ხელახლა ცდა',
              // `FuzzzyButton.ghost`: `control` in `ink` — this is the only
              // way out of the error state, so it must not read as disabled.
              style: type.control.copyWith(color: colors.ink),
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
      // The sheet draws its OWN `raised` + `lineStrong` box and its own top
      // corners (M5's feedback_sheet idiom), so the route must not paint a
      // second one underneath it.
      backgroundColor: Colors.transparent,
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
