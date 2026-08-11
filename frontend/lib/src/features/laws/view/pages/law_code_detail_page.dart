import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

/// Shows the structure of a single legal code (chapters + articles).
class LawCodeDetailPage extends StatelessWidget {
  final LawCode code;

  const LawCodeDetailPage({super.key, required this.code});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // Title style comes from appBarTheme (titleM + ink), built from roles.
        title: Text(code.name, maxLines: 1, overflow: TextOverflow.ellipsis),
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
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
            Icon(Icons.article_outlined, size: 48, color: colors.inkFaint),
            SizedBox(height: space.l),
            Text(
              'სტრუქტურა ვერ მოიძებნა',
              style: type.body.copyWith(color: colors.inkMute),
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
      padding: density.screen,
      itemCount: articleKeys.length,
      separatorBuilder: (_, __) => SizedBox(height: space.xs),
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
            color: colors.surface,
            border: Border.all(color: colors.line),
            borderRadius: BorderRadius.circular(radius.l),
          ),
          child: ListTile(
            contentPadding: density.tile,
            title: Text(
              title,
              style: type.titleS.copyWith(color: colors.ink),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Padding(
              padding: EdgeInsets.only(top: space.xs),
              child: Text(
                snippet,
                style: type.bodyS.copyWith(color: colors.inkMute),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            trailing: Icon(Icons.chevron_right, color: colors.inkMute, size: 20),
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
            'ჩატვირთვა ვერ მოხერხდა',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.l),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadCodeStructure(code.id),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
