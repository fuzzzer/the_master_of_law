import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

/// Displays full article text with formatted legal content.
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
            onSuccess: () => _buildArticleContent(context, state),
            onFailure: () => _buildError(context),
          );
        },
      ),
    );
  }

  Widget _buildArticleContent(BuildContext context, LawsState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final article = state.selectedArticle;
    if (article == null) return const SizedBox.shrink();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Code name badge
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
          // Article title
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
          // Article content
          SelectableText(
            article.combinedContent,
            style: uiTextStyles.body14.copyWith(
              color: uiColors.primaryTextColor,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 32),
          // Metadata
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
    final state = context.read<LawsCubit>().state;
    final article = state.selectedArticle;
    if (article == null) return;

    Clipboard.setData(ClipboardData(text: article.combinedContent));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('ტექსტი დაკოპირდა'), duration: Duration(seconds: 2)),
    );
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
          Text(
            'მუხლის ჩატვირთვა ვერ მოხერხდა',
            style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
          ),
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
