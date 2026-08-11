import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

/// Laws browser home page — lists all legal codes with search.
class LawsHomePage extends StatelessWidget {
  const LawsHomePage({super.key});

  static const _codeIcons = <String, String>{
    'სამოქალაქო': '🏛️',
    'სისხლის': '⚖️',
    'ადმინისტრაციულ': '📋',
    'შრომის': '👷',
    'საგადასახადო': '💰',
    'ოჯახის': '👨‍👩‍👧',
    'საკუთრების': '🏠',
    'კონსტიტუცია': '📜',
    'საპროცესო': '📄',
    'სამეწარმეო': '🏢',
  };

  String _iconForCode(String codeName) {
    for (final entry in _codeIcons.entries) {
      if (codeName.contains(entry.key)) return entry.value;
    }
    return '📚';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // Title style comes from appBarTheme (titleM + ink), built from roles.
        title: const Text('კანონები'),
        actions: [
          IconButton(
            // Icon colour comes from appBarTheme.actionsIconTheme (ink).
            icon: const Icon(Icons.search),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => BlocProvider.value(
                    value: context.read<LawsCubit>(),
                    child: const LawSearchPage(),
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: BlocBuilder<LawsCubit, LawsState>(
        buildWhen: (prev, curr) =>
            prev.codesStatus != curr.codesStatus || prev.codes != curr.codes,
        builder: (context, state) {
          return StatusBuilder.buildByStatus(
            status: state.codesStatus,
            onInitial: () => const SizedBox.shrink(),
            onLoading: () => const Center(child: CircularProgressIndicator()),
            onSuccess: () => _buildCodesList(context, state),
            onFailure: () => _buildErrorState(context, state),
          );
        },
      ),
    );
  }

  Widget _buildCodesList(BuildContext context, LawsState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return ListView(
      padding: density.screen,
      children: [
        // Search banner
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () {
            Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => BlocProvider.value(
                  value: context.read<LawsCubit>(),
                  child: const LawSearchPage(),
                ),
              ),
            );
          },
          child: Container(
            padding: density.card,
            decoration: BoxDecoration(
              color: colors.surface,
              borderRadius: BorderRadius.circular(radius.l),
              border: Border.all(color: colors.line),
            ),
            child: Row(
              children: [
                Icon(Icons.search, color: colors.ink),
                SizedBox(width: space.m),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'მოძებნეთ კანონი',
                        style: type.titleS.copyWith(color: colors.ink),
                      ),
                      Text(
                        '${state.codes.fold<int>(0, (sum, c) => sum + c.articleCount)} სტატია ინდექსირებულია',
                        style: type.bodyS.copyWith(color: colors.inkMute),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        SizedBox(height: space.xl),
        Text('კოდექსები', style: type.titleS.copyWith(color: colors.ink)),
        SizedBox(height: space.m),
        ...state.codes.map((code) => Padding(
              padding: EdgeInsets.only(bottom: space.s),
              child: Container(
                decoration: BoxDecoration(
                  color: colors.surface,
                  border: Border.all(color: colors.line),
                  borderRadius: BorderRadius.circular(radius.l),
                ),
                child: ListTile(
                  // The emoji IS text, so it takes a type role rather than a
                  // literal fontSize (guard: literal-font-size is BLOCKING).
                  leading: Text(_iconForCode(code.name), style: type.titleL),
                  title: Text(
                    code.name,
                    style: type.titleS.copyWith(color: colors.ink),
                  ),
                  subtitle: Text(
                    '${code.articleCount} მუხლი',
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                  trailing: Icon(Icons.chevron_right, color: colors.inkMute),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.l),
                  ),
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => BlocProvider.value(
                          value: context.read<LawsCubit>()..loadCodeStructure(code.id),
                          child: LawCodeDetailPage(code: code),
                        ),
                      ),
                    );
                  },
                ),
              ),
            )),
      ],
    );
  }

  Widget _buildErrorState(BuildContext context, LawsState state) {
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
            'მონაცემების ჩატვირთვა ვერ მოხერხდა',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.s),
          Text(
            'სცადეთ ხელახლა',
            style: type.bodyS.copyWith(color: colors.inkMute),
          ),
          SizedBox(height: space.l),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadCodes(),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
