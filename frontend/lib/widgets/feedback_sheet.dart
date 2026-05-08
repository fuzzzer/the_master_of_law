import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Bottom sheet for submitting feedback on a case or conversation.
///
/// Shows category selector chips, 1-5 star rating, comment field,
/// optional section selector, and submit button.
///
/// Usage:
/// ```dart
/// showModalBottomSheet(
///   context: context,
///   isScrollControlled: true,
///   builder: (_) => FeedbackSheet(
///     targetType: 'case_file',
///     targetId: caseData.id,
///     onSubmitted: () { /* refresh list */ },
///   ),
/// );
/// ```
class FeedbackSheet extends StatefulWidget {
  const FeedbackSheet({
    super.key,
    required this.targetType,
    required this.targetId,
    this.onSubmitted,
  });

  final String targetType;
  final String targetId;
  final VoidCallback? onSubmitted;

  @override
  State<FeedbackSheet> createState() => _FeedbackSheetState();
}

class _FeedbackSheetState extends State<FeedbackSheet> {
  String _selectedCategory = 'overall';
  int _rating = 0;
  final _commentController = TextEditingController();
  final _sectionController = TextEditingController();
  bool _isSubmitting = false;

  static const List<String> _categories = [
    'accuracy',
    'completeness',
    'relevance',
    'formatting',
    'citation_quality',
    'legal_reasoning',
    'overall',
  ];

  static const Map<String, String> _categoryLabels = {
    'accuracy': 'სიზუსტე',
    'completeness': 'სრულყოფილება',
    'relevance': 'რელევანტურობა',
    'formatting': 'ფორმატირება',
    'citation_quality': 'ციტირება',
    'legal_reasoning': 'იურიდ. არგუმენტაცია',
    'overall': 'საერთო',
  };

  @override
  void dispose() {
    _commentController.dispose();
    _sectionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Title
          Text(
            'შეფასება',
            style: uiTextStyles.headlineBold20.copyWith(
              color: uiColors.primaryTextColor,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'თქვენი აზრი მნიშვნელოვანია ხარისხის გასაუმჯობესებლად',
            style: uiTextStyles.caption11.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 20),
          // Category chips
          Text(
            'კატეგორია:',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _categories.map((cat) {
              final isSelected = cat == _selectedCategory;
              return GestureDetector(
                onTap: () => setState(() => _selectedCategory = cat),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? uiColors.accentColor.withValues(alpha: 0.15)
                        : uiColors.surfaceColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: isSelected
                          ? uiColors.accentColor
                          : uiColors.secondaryTextColor.withValues(alpha: 0.2),
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Text(
                    _categoryLabels[cat] ?? cat,
                    style: uiTextStyles.labelBold12.copyWith(
                      color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          // Star rating
          Text(
            'რეიტინგი:',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: List.generate(5, (index) {
              final starIndex = index + 1;
              return GestureDetector(
                onTap: () => setState(() => _rating = starIndex),
                child: Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Icon(
                    starIndex <= _rating ? Icons.star_rounded : Icons.star_border_rounded,
                    color: starIndex <= _rating ? uiColors.warningColor : uiColors.secondaryTextColor,
                    size: 32,
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 20),
          // Comment field
          Text(
            'კომენტარი:',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _commentController,
            maxLines: 4,
            maxLength: 2000,
            style: uiTextStyles.body16.copyWith(color: uiColors.primaryTextColor),
            decoration: InputDecoration(
              hintText: 'დაწერეთ მინიმუმ 10 სიმბოლო...',
              hintStyle: uiTextStyles.body16.copyWith(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: uiColors.secondaryTextColor.withValues(alpha: 0.2),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Optional section
          Text(
            'კონკრეტული სექცია (არასავალდებულო):',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _sectionController,
            maxLength: 100,
            style: uiTextStyles.body16.copyWith(color: uiColors.primaryTextColor),
            decoration: InputDecoration(
              hintText: 'მაგ: მტკიცებულებები',
              hintStyle: uiTextStyles.body16.copyWith(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
              ),
            ),
          ),
          const SizedBox(height: 24),
          // Submit button
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: (_rating == 0 || _isSubmitting) ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: uiColors.accentColor,
                foregroundColor: uiColors.backgroundPrimaryColor,
                disabledBackgroundColor: uiColors.accentColor.withValues(alpha: 0.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                textStyle: uiTextStyles.bodyBold16,
              ),
              child: _isSubmitting
                  ? SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: uiColors.backgroundPrimaryColor,
                      ),
                    )
                  : const Text('გაგზავნა →'),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    final comment = _commentController.text.trim();
    if (comment.isNotEmpty && comment.length < 10) {
      _showToast('კომენტარი მინიმუმ 10 სიმბოლო უნდა იყოს');
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      // TODO: Wire to actual API client when integration is done
      // final client = context.read<TheMasterOfLawHttpClient>();
      // await client.post('/api/v1/feedback', data: {...});

      await Future.delayed(const Duration(milliseconds: 800)); // simulate

      if (!mounted) return;
      Navigator.pop(context);
      _showToast('შეფასება მიღებულია — გმადლობთ!');
      widget.onSubmitted?.call();
    } catch (e) {
      if (!mounted) return;
      _showToast('შეცდომა: ვერ მოხერხდა გაგზავნა');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showToast(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
