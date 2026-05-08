import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'კანონები',
          style: uiTextStyles.headlineBold20.copyWith(color: uiColors.accentColor),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.search, color: uiColors.secondaryTextColor),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Search banner
        GestureDetector(
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
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: uiColors.accentColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.2)),
            ),
            child: Row(
              children: [
                Icon(Icons.search, color: uiColors.accentColor),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'მოძებნეთ კანონი',
                        style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor),
                      ),
                      Text(
                        '${state.codes.fold<int>(0, (sum, c) => sum + c.articleCount)} სტატია ინდექსირებულია',
                        style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'კოდექსები',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        const SizedBox(height: 12),
        ...state.codes.map((code) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Container(
                decoration: BoxDecoration(
                  color: uiColors.backgroundSecondaryColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ListTile(
                  leading: Text(_iconForCode(code.name), style: const TextStyle(fontSize: 28)),
                  title: Text(
                    code.name,
                    style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                  ),
                  subtitle: Text(
                    '${code.articleCount} მუხლი',
                    style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                  ),
                  trailing: Icon(Icons.chevron_right, color: uiColors.secondaryTextColor),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
          const SizedBox(height: 16),
          Text(
            'მონაცემების ჩატვირთვა ვერ მოხერხდა',
            style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 8),
          Text(
            'სცადეთ ხელახლა',
            style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.read<LawsCubit>().loadCodes(),
            child: const Text('ხელახლა ცდა'),
          ),
        ],
      ),
    );
  }
}
