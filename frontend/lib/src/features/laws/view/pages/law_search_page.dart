import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

class LawSearchPage extends StatefulWidget {
  const LawSearchPage({super.key});

  @override
  State<LawSearchPage> createState() => _LawSearchPageState();
}

class _LawSearchPageState extends State<LawSearchPage> {
  final _searchController = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _focusNode.requestFocus();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _searchController,
          focusNode: _focusNode,
          style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
          decoration: InputDecoration(
            hintText: 'მოძებნეთ კანონი...',
            hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            border: InputBorder.none,
          ),
          onChanged: (query) => context.read<LawsCubit>().searchLawsDebounced(query),
        ),
        actions: [
          BlocBuilder<LawsCubit, LawsState>(
            buildWhen: (prev, curr) => prev.searchQuery != curr.searchQuery,
            builder: (context, state) {
              if (state.searchQuery.isEmpty) return const SizedBox.shrink();
              return IconButton(
                icon: Icon(Icons.clear, color: uiColors.secondaryTextColor),
                onPressed: () {
                  _searchController.clear();
                  context.read<LawsCubit>().clearSearch();
                },
              );
            },
          ),
        ],
      ),
      body: BlocBuilder<LawsCubit, LawsState>(
        buildWhen: (prev, curr) =>
            prev.searchStatus != curr.searchStatus ||
            prev.searchResults != curr.searchResults ||
            prev.searchQuery != curr.searchQuery,
        builder: (context, state) {
          if (state.searchQuery.isEmpty || state.searchQuery.length < 2) {
            return _buildHint(context);
          }
          return StatusBuilder.buildByStatus(
            status: state.searchStatus,
            onInitial: () => _buildHint(context),
            onLoading: () => const Center(child: CircularProgressIndicator()),
            onSuccess: () => _buildResults(context, state),
            onFailure: () => _buildSearchError(context),
          );
        },
      ),
    );
  }

  Widget _buildHint(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search, size: 64, color: uiColors.secondaryTextColor.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          Text('შეიყვანეთ მინიმუმ 2 სიმბოლო',
              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
        ],
      ),
    );
  }

  Widget _buildResults(BuildContext context, LawsState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final results = state.searchResults;

    if (results == null || results.results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 48, color: uiColors.secondaryTextColor.withValues(alpha: 0.4)),
            const SizedBox(height: 16),
            Text('შედეგები ვერ მოიძებნა',
                style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
            const SizedBox(height: 8),
            Text('სცადეთ სხვა საძიებო სიტყვები',
                style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Text('${results.total} შედეგი',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: results.results.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) => _buildResultCard(context, results.results[index]),
          ),
        ),
      ],
    );
  }

  Widget _buildResultCard(BuildContext context, LawChunk chunk) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    final title = chunk.articleTitle.isNotEmpty
        ? chunk.articleTitle
        : chunk.articleNumber.isNotEmpty
            ? 'მუხლი ${chunk.articleNumber}'
            : chunk.chunkId;
    final snippet = chunk.content.length > 200 ? '${chunk.content.substring(0, 200)}…' : chunk.content;

    return Container(
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(10),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        title: Row(
          children: [
            Expanded(
              child: Text(title,
                  style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                  maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
            if (chunk.codeName.isNotEmpty) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: uiColors.accentColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(chunk.codeName,
                    style: uiTextStyles.caption11.copyWith(color: uiColors.accentColor, fontSize: 9),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
              ),
            ],
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Text(snippet,
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
              maxLines: 3, overflow: TextOverflow.ellipsis),
        ),
        onTap: () {
          final articleId = chunk.articleNumber.isNotEmpty ? chunk.articleNumber : chunk.chunkId;
          Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => BlocProvider.value(
                value: context.read<LawsCubit>()..loadArticle(articleId),
                child: LawArticlePage(articleId: articleId, articleTitle: title, codeName: chunk.codeName),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSearchError(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
          const SizedBox(height: 16),
          Text('ძიება ვერ მოხერხდა',
              style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().searchLawsDebounced(_searchController.text),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
