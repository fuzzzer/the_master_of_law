import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;

    return Scaffold(
      appBar: AppBar(
        // This field is app-bar CHROME, not a form field: it must opt OUT of
        // inputDecorationTheme's box (fill + four border states + padding),
        // which would otherwise draw a full outlined field inside the AppBar.
        // Declaring absence is not "re-declaring a border" — hintStyle still
        // comes from the theme.
        title: TextField(
          controller: _searchController,
          focusNode: _focusNode,
          style: type.body.copyWith(color: colors.fieldText),
          decoration: const InputDecoration(
            hintText: 'მოძებნეთ კანონი...',
            filled: false,
            border: InputBorder.none,
            enabledBorder: InputBorder.none,
            focusedBorder: InputBorder.none,
            contentPadding: EdgeInsets.zero,
          ),
          onChanged: (query) => context.read<LawsCubit>().searchLawsDebounced(query),
        ),
        actions: [
          BlocBuilder<LawsCubit, LawsState>(
            buildWhen: (prev, curr) => prev.searchQuery != curr.searchQuery,
            builder: (context, state) {
              if (state.searchQuery.isEmpty) return const SizedBox.shrink();
              return IconButton(
                // Inherits appBarTheme.actionsIconTheme (ink): clearing the
                // query is the bar's only affordance, so it is not demoted.
                icon: const Icon(Icons.clear),
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search, size: 64, color: colors.inkFaint),
          SizedBox(height: space.l),
          Text('შეიყვანეთ მინიმუმ 2 სიმბოლო',
              style: type.body.copyWith(color: colors.inkMute)),
        ],
      ),
    );
  }

  Widget _buildResults(BuildContext context, LawsState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;
    final results = state.searchResults;

    if (results == null || results.results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 48, color: colors.inkFaint),
            SizedBox(height: space.l),
            Text('შედეგები ვერ მოიძებნა',
                style: type.titleS.copyWith(color: colors.ink)),
            SizedBox(height: space.s),
            Text('სცადეთ სხვა საძიებო სიტყვები',
                style: type.bodyS.copyWith(color: colors.inkMute)),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          // Screen inset horizontally so the header aligns with the cards.
          padding: density.screen.copyWith(top: space.m, bottom: space.s),
          child: Text('${results.total} შედეგი',
              style: type.bodyS.copyWith(color: colors.inkMute)),
        ),
        Expanded(
          child: ListView.separated(
            padding: density.screen.copyWith(top: 0, bottom: 0),
            itemCount: results.results.length,
            separatorBuilder: (_, __) => SizedBox(height: space.s),
            itemBuilder: (context, index) => _buildResultCard(context, results.results[index]),
          ),
        ),
      ],
    );
  }

  Widget _buildResultCard(BuildContext context, LawChunk chunk) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final title = chunk.articleTitle.isNotEmpty
        ? chunk.articleTitle
        : chunk.articleNumber.isNotEmpty
            ? 'მუხლი ${chunk.articleNumber}'
            : chunk.chunkId;
    final snippet = chunk.content.length > 200 ? '${chunk.content.substring(0, 200)}…' : chunk.content;

    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border.all(color: colors.line),
        borderRadius: BorderRadius.circular(radius.l),
      ),
      child: ListTile(
        contentPadding: density.tile,
        title: Row(
          children: [
            Expanded(
              child: Text(title,
                  style: type.titleS.copyWith(color: colors.ink),
                  maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
            if (chunk.codeName.isNotEmpty) ...[
              SizedBox(width: space.s),
              // Flexible, not fixed: the badge grew from a 9pt literal to the
              // smallest Georgian-capable role, so it must be able to yield
              // rather than squeeze the title to nothing.
              Flexible(
                child: Container(
                  padding: density.chip,
                  decoration: BoxDecoration(
                    // Recessed well: this pill sits ON a surface card.
                    color: colors.ground,
                    border: Border.all(color: colors.line),
                    borderRadius: BorderRadius.circular(radius.s),
                  ),
                  child: Text(chunk.codeName,
                      style: type.bodyS.copyWith(color: colors.ink),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                ),
              ),
            ],
          ],
        ),
        subtitle: Padding(
          padding: EdgeInsets.only(top: space.xs),
          child: Text(snippet,
              style: type.bodyS.copyWith(color: colors.inkMute),
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: colors.inkFaint),
          SizedBox(height: space.l),
          Text('ძიება ვერ მოხერხდა',
              style: type.titleS.copyWith(color: colors.ink)),
          SizedBox(height: space.l),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().searchLawsDebounced(_searchController.text),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
