import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'იურიდიული ლექსიკონი',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
              decoration: InputDecoration(
                hintText: 'მოძებნეთ ტერმინი...',
                hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                prefixIcon: Icon(Icons.search, color: uiColors.secondaryTextColor),
                filled: true,
                fillColor: uiColors.backgroundSecondaryColor,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
          Expanded(
            child: _filteredTerms.isEmpty
                ? Center(
                    child: Text(
                      'ტერმინი ვერ მოიძებნა',
                      style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: _filteredTerms.length,
                    separatorBuilder: (context, index) => Divider(color: uiColors.backgroundSecondaryColor),
                    itemBuilder: (context, index) {
                      final term = _filteredTerms[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              term.term,
                              style: uiTextStyles.bodyBold16.copyWith(color: uiColors.accentColor),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              term.definition,
                              style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
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
