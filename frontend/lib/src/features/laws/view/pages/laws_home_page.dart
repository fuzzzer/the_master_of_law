import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/core/core.dart';

/// Laws browser home page — lists all legal codes with search.
class LawsHomePage extends StatelessWidget {
  const LawsHomePage({super.key});

  static const _legalCodes = [
    ('🏛️', 'სამოქალაქო კოდექსი', 'Civil Code'),
    ('⚖️', 'სისხლის სამართლის კოდექსი', 'Criminal Code'),
    ('📋', 'ადმინისტრაციულ სამართალდარღვევათა კოდექსი', 'Administrative Code'),
    ('👷', 'შრომის კოდექსი', 'Labor Code'),
    ('💰', 'საგადასახადო კოდექსი', 'Tax Code'),
    ('👨‍👩‍👧', 'ოჯახის კანონი', 'Family Law'),
    ('🏠', 'საკუთრების კანონი', 'Property Law'),
    ('📜', 'კონსტიტუცია', 'Constitution'),
  ];

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
              // TODO: Search across all codes
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Search banner
          Container(
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
                        '9,450 სტატია ინდექსირებულია',
                        style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'კოდექსები',
            style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 12),
          ...List.generate(_legalCodes.length, (index) {
            final (icon, titleKa, titleEn) = _legalCodes[index];
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Container(
                decoration: BoxDecoration(
                  color: uiColors.backgroundSecondaryColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ListTile(
                  leading: Text(icon, style: const TextStyle(fontSize: 28)),
                  title: Text(
                    titleKa,
                    style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                  ),
                  subtitle: Text(
                    titleEn,
                    style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                  ),
                  trailing: Icon(Icons.chevron_right, color: uiColors.secondaryTextColor),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  onTap: () {
                    // TODO: Navigate to code structure
                  },
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
