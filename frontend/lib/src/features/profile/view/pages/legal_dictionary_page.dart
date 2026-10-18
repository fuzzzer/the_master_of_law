import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'legal_dictionary_data.dart';

class LegalDictionaryPage extends StatefulWidget {
  const LegalDictionaryPage({super.key});

  @override
  State<LegalDictionaryPage> createState() => _LegalDictionaryPageState();
}

class _LegalDictionaryPageState extends State<LegalDictionaryPage> {
  final TextEditingController _searchController = TextEditingController();
  List<LegalTerm> _filteredTerms = [];

  @override
  void initState() {
    super.initState();
    _filteredTerms = legalDictionaryData;
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      if (query.isEmpty) {
        _filteredTerms = legalDictionaryData;
      } else {
        _filteredTerms = legalDictionaryData.where((term) {
          return term.term.toLowerCase().contains(query) ||
              term.definition.toLowerCase().contains(query);
        }).toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;

    return Scaffold(
      // Title style comes from appBarTheme (titleM + ink), built from roles.
      appBar: AppBar(title: const Text('იურიდიული ლექსიკონი')),
      body: Column(
        children: [
          Padding(
            padding: density.screen,
            child: TextField(
              controller: _searchController,
              style: type.body.copyWith(color: colors.fieldText),
              // fill, borders, contentPadding and hintStyle all come from
              // inputDecorationTheme, which is built from the ten kit form
              // colour roles. Nothing about the box is restated here.
              decoration: InputDecoration(
                hintText: 'მოძებნეთ ტერმინი...',
                prefixIcon: Icon(Icons.search, color: colors.inkMute),
              ),
            ),
          ),
          Expanded(
            child: _filteredTerms.isEmpty
                ? Center(
                    child: Text(
                      'ტერმინი ვერ მოიძებნა',
                      style: type.body.copyWith(color: colors.inkMute),
                    ),
                  )
                : ListView.separated(
                    // Same screen inset as the search field above it, so the
                    // two columns align; tighter vertically because the list
                    // already separates its own rows.
                    padding: density.screen.copyWith(
                      top: space.s,
                      bottom: space.s,
                    ),
                    itemCount: _filteredTerms.length,
                    separatorBuilder: (context, index) => const Divider(),
                    itemBuilder: (context, index) {
                      final term = _filteredTerms[index];
                      return Padding(
                        padding: EdgeInsets.symmetric(vertical: space.s),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              term.term,
                              style: type.titleS.copyWith(color: colors.ink),
                            ),
                            SizedBox(height: space.xs),
                            Text(
                              term.definition,
                              style: type.body.copyWith(color: colors.ink),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
