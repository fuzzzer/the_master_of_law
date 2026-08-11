import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

class LawArticlePage extends StatelessWidget {
  final String articleId;
  final String articleTitle;
  final String codeName;

  const LawArticlePage({
    super.key,
    required this.articleId,
    required this.articleTitle,
    required this.codeName,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;

    return Scaffold(
      appBar: AppBar(
        // Title style comes from appBarTheme (titleM + ink), built from roles.
        title: Text(articleTitle, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            // Primary action: inherits appBarTheme.actionsIconTheme (ink).
            icon: const Icon(Icons.bookmark_add_outlined, size: 22),
            onPressed: () => _showSaveToCaseSheet(context),
          ),
          IconButton(
            // Secondary action, deliberately demoted one rung.
            icon: Icon(Icons.copy, color: colors.inkMute, size: 20),
            onPressed: () => _copyContent(context),
          ),
        ],
      ),
      body: BlocBuilder<LawsCubit, LawsState>(
        buildWhen: (prev, curr) =>
            prev.articleStatus != curr.articleStatus ||
            prev.selectedArticle != curr.selectedArticle,
        builder: (context, state) {
          return StatusBuilder.buildByStatus(
            status: state.articleStatus,
            onInitial: () => const SizedBox.shrink(),
            onLoading: () => const Center(child: CircularProgressIndicator()),
            onSuccess: () => _buildContent(context, state),
            onFailure: () => _buildError(context),
          );
        },
      ),
    );
  }

  Widget _buildContent(BuildContext context, LawsState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final article = state.selectedArticle;
    if (article == null) return const SizedBox.shrink();

    return SingleChildScrollView(
      padding: density.screen,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: density.chip,
            decoration: BoxDecoration(
              color: colors.surface,
              border: Border.all(color: colors.line),
              borderRadius: BorderRadius.circular(radius.s),
            ),
            child: Text(
              codeName.isNotEmpty ? codeName : article.codeName,
              style: type.bodyS.copyWith(color: colors.ink),
            ),
          ),
          SizedBox(height: space.m),
          Text(
            article.articleTitle.isNotEmpty
                ? article.articleTitle
                : articleTitle,
            style: type.titleM.copyWith(color: colors.ink),
          ),
          if (article.articleNumber.isNotEmpty) ...[
            SizedBox(height: space.xs),
            Text(
              'მუხლი ${article.articleNumber}',
              style: type.body.copyWith(color: colors.inkMute),
            ),
          ],
          SizedBox(height: space.xl),
          SelectableText(
            article.combinedContent,
            // No `height:` override — the pack owns the type scale, and
            // `body` already carries the long-form line height (1.55).
            style: type.body.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.xxl),
          if (article.chunks.isNotEmpty) ...[
            // Divider colour comes from dividerTheme (line).
            const Divider(),
            SizedBox(height: space.s),
            Text(
              '${article.total} ფრაგმენტი',
              style: type.bodyS.copyWith(color: colors.inkMute),
            ),
          ],
        ],
      ),
    );
  }

  void _copyContent(BuildContext context) {
    final article = context.read<LawsCubit>().state.selectedArticle;
    if (article == null) return;
    Clipboard.setData(ClipboardData(text: article.combinedContent));
    // M11: the dwell is no longer ours to state — FuzzzyToast owns it.
    FuzzzyToast.show(
      context,
      message: 'ტექსტი დაკოპირდა',
      kind: FuzzzyToastKind.success,
      qaId: 'law.article.copied',
    );
  }

  void _showSaveToCaseSheet(BuildContext context) {
    final article = context.read<LawsCubit>().state.selectedArticle;
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    showModalBottomSheet<void>(
      context: context,
      builder: (_) => BlocProvider(
        create: (_) => CasesCubit(
          repository: CaseRepository(localDataSource: CaseLocalDataSource()),
        )..loadCases(),
        child: BlocBuilder<CasesCubit, CasesState>(
          builder: (sheetContext, casesState) {
            if (casesState.status == StateStatus.loading) {
              // Dimension, not a gap: the sheet's reserved loading height, so
              // it does not collapse and re-expand around the spinner.
              return const SizedBox(
                height: 200,
                child: Center(child: CircularProgressIndicator()),
              );
            }

            final cases = casesState.cases;

            return SafeArea(
              child: Padding(
                padding: density.dialog,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'შეინახეთ საქმეში',
                      style: type.titleM.copyWith(color: colors.ink),
                    ),
                    SizedBox(height: space.l),
                    if (cases.isEmpty)
                      Padding(
                        padding: EdgeInsets.symmetric(vertical: space.xl),
                        child: Center(
                          child: Text(
                            'საქმეები ვერ მოიძებნა',
                            style: type.body.copyWith(color: colors.inkMute),
                          ),
                        ),
                      )
                    else
                      ...cases.map(
                        (caseData) => ListTile(
                          leading: Icon(
                            Icons.folder_special,
                            color: colors.ink,
                          ),
                          title: Text(
                            caseData.title,
                            style: type.titleS.copyWith(color: colors.ink),
                          ),
                          subtitle: Text(
                            '${caseData.linkedArticles.length} მუხლი შენახული',
                            style: type.bodyS.copyWith(color: colors.inkMute),
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(radius.m),
                          ),
                          onTap: () => _saveToCase(context, caseData, article),
                        ),
                      ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _saveToCase(
    BuildContext context,
    CaseData caseData,
    LawArticleDetail? article,
  ) {
    final snippet = article != null && article.combinedContent.length > 100
        ? '${article.combinedContent.substring(0, 100)}…'
        : article?.combinedContent ?? '';

    final linkedArticle = LinkedArticleData(
      articleId: articleId,
      title: article?.articleTitle.isNotEmpty == true
          ? article!.articleTitle
          : articleTitle,
      codeName: codeName.isNotEmpty ? codeName : (article?.codeName ?? ''),
      snippet: snippet,
      savedAt: DateTime.now(),
    );

    // Save via a fresh cubit instance
    final cubit = CaseDetailCubit(
      repository: CaseRepository(localDataSource: CaseLocalDataSource()),
    );
    cubit.loadCase(caseData.id).then((_) {
      cubit.linkArticle(linkedArticle).then((_) {
        cubit.close();
        if (!context.mounted) return;
        Navigator.of(context).pop();
        FuzzzyToast.show(
          context,
          message: 'შენახულია: ${caseData.title}',
          kind: FuzzzyToastKind.success,
          qaId: 'law.article.saved',
        );
      });
    });
  }

  Widget _buildError(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: colors.inkFaint),
          SizedBox(height: space.l),
          Text(
            'მუხლის ჩატვირთვა ვერ მოხერხდა',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.l),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadArticle(articleId),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
