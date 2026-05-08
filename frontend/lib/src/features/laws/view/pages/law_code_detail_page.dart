import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

/// Shows the structure of a single legal code (chapters + articles).
class LawCodeDetailPage extends StatelessWidget {
  final LawCode code;

  const LawCodeDetailPage({super.key, required this.code});

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          code.name,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: BlocBuilder<LawsCubit, LawsState>(
        buildWhen: (prev, curr) =>
            prev.structureStatus != curr.structureStatus ||
            prev.selectedCodeStructure != curr.selectedCodeStructure,
        builder: (context, state) {
          return StatusBuilder.buildByStatus(
            status: state.structureStatus,
            onInitial: () => const SizedBox.shrink(),
            onLoading: () => const Center(child: CircularProgressIndicator()),
            onSuccess: () => _buildStructure(context, state),
            onFailure: () => _buildError(context),
          );
        },
      ),
    );
  }

  Widget _buildStructure(BuildContext context, LawsState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final structure = state.selectedCodeStructure;
    if (structure == null) return const SizedBox.shrink();

    // Extract article chunks from the structure response
    final rawChunks = structure['chunks'] as List<dynamic>? ??
        structure['articles'] as List<dynamic>? ??
        [];

    if (rawChunks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.article_outlined, size: 48, color: uiColors.secondaryTextColor),
            const SizedBox(height: 16),
            Text(
              'სტრუქტურა ვერ მოიძებნა',
              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            ),
          ],
        ),
      );
    }

    // Group chunks by article_number
    final articleGroups = <String, List<LawChunk>>{};
    for (final raw in rawChunks) {
      final chunk = LawChunk.fromMap(raw as Map<String, dynamic>);
      final key = chunk.articleNumber.isNotEmpty ? chunk.articleNumber : chunk.chunkId;
      articleGroups.putIfAbsent(key, () => []).add(chunk);
    }

    final articleKeys = articleGroups.keys.toList();

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: articleKeys.length,
      separatorBuilder: (_, __) => const SizedBox(height: 4),
      itemBuilder: (context, index) {
        final articleNumber = articleKeys[index];
        final chunks = articleGroups[articleNumber]!;
        final firstChunk = chunks.first;
        final title = firstChunk.articleTitle.isNotEmpty
            ? firstChunk.articleTitle
            : 'მუხლი $articleNumber';
        final snippet = firstChunk.content.length > 120
            ? '${firstChunk.content.substring(0, 120)}…'
            : firstChunk.content;

        return Container(
          decoration: BoxDecoration(
            color: uiColors.backgroundSecondaryColor,
            borderRadius: BorderRadius.circular(10),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            title: Text(
              title,
              style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                snippet,
                style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            trailing: Icon(Icons.chevron_right, color: uiColors.secondaryTextColor, size: 20),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => BlocProvider.value(
                    value: context.read<LawsCubit>()..loadArticle(articleNumber),
                    child: LawArticlePage(
                      articleId: articleNumber,
                      articleTitle: title,
                      codeName: code.name,
                    ),
                  ),
                ),
              );
            },
          ),
        );
      },
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
            'ჩატვირთვა ვერ მოხერხდა',
            style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadCodeStructure(code.id),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
