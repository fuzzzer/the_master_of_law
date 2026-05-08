import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/cases/cases.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          articleTitle,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.bookmark_add_outlined, color: uiColors.accentColor, size: 22),
            onPressed: () => _showSaveToCaseSheet(context),
          ),
          IconButton(
            icon: Icon(Icons.copy, color: uiColors.secondaryTextColor, size: 20),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final article = state.selectedArticle;
    if (article == null) return const SizedBox.shrink();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: uiColors.accentColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              codeName.isNotEmpty ? codeName : article.codeName,
              style: uiTextStyles.caption11.copyWith(color: uiColors.accentColor),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            article.articleTitle.isNotEmpty ? article.articleTitle : articleTitle,
            style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
          ),
          if (article.articleNumber.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              'მუხლი ${article.articleNumber}',
              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            ),
          ],
          const SizedBox(height: 20),
          SelectableText(
            article.combinedContent,
            style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor, height: 1.6),
          ),
          const SizedBox(height: 32),
          if (article.chunks.isNotEmpty) ...[
            Divider(color: uiColors.secondaryTextColor.withValues(alpha: 0.2)),
            const SizedBox(height: 8),
            Text(
              '${article.total} ფრაგმენტი',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
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
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('ტექსტი დაკოპირდა'), duration: Duration(seconds: 2)),
    );
  }

  void _showSaveToCaseSheet(BuildContext context) {
    final article = context.read<LawsCubit>().state.selectedArticle;
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    showModalBottomSheet<void>(
      context: context,
      builder: (_) => BlocProvider(
        create: (_) => CasesCubit(
          repository: CaseRepository(localDataSource: CaseLocalDataSource()),
        )..loadCases(),
        child: BlocBuilder<CasesCubit, CasesState>(
          builder: (sheetContext, casesState) {
            if (casesState.status == StateStatus.loading) {
              return const SizedBox(height: 200, child: Center(child: CircularProgressIndicator()));
            }

            final cases = casesState.cases;

            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('შეინახეთ საქმეში',
                        style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                    const SizedBox(height: 16),
                    if (cases.isEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 24),
                        child: Center(
                          child: Text('საქმეები ვერ მოიძებნა',
                              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
                        ),
                      )
                    else
                      ...cases.map((caseData) => ListTile(
                            leading: Icon(Icons.folder_special, color: uiColors.accentColor),
                            title: Text(caseData.title,
                                style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
                            subtitle: Text('${caseData.linkedArticles.length} მუხლი შენახული',
                                style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            onTap: () => _saveToCase(context, caseData, article),
                          )),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _saveToCase(BuildContext context, CaseData caseData, LawArticleDetail? article) {
    final snippet = article != null && article.combinedContent.length > 100
        ? '${article.combinedContent.substring(0, 100)}…'
        : article?.combinedContent ?? '';

    final linkedArticle = LinkedArticleData(
      articleId: articleId,
      title: article?.articleTitle.isNotEmpty == true ? article!.articleTitle : articleTitle,
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
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('შენახულია: ${caseData.title}'),
            duration: const Duration(seconds: 2),
          ),
        );
      });
    });
  }

  Widget _buildError(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
          const SizedBox(height: 16),
          Text('მუხლის ჩატვირთვა ვერ მოხერხდა',
              style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadArticle(articleId),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
