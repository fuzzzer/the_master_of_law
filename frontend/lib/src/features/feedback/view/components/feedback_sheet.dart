import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Bottom sheet for submitting feedback on a case or conversation.
/// Shows category chips, 1-5 star rating, optional comment, and submit button.
class FeedbackSheet extends StatefulWidget {
  const FeedbackSheet({
    super.key,
    required this.targetId,
    required this.targetType,
    this.specificSection,
  });

  final String targetId;
  final FeedbackTargetType targetType;
  final String? specificSection;

  static Future<void> show(
    BuildContext context, {
    required String targetId,
    required FeedbackTargetType targetType,
    String? specificSection,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => BlocProvider(
        create: (_) => FeedbackCubit(
          repository: FeedbackRepository(
            remoteDataSource: FeedbackRemoteDataSource(),
          ),
        ),
        child: FeedbackSheet(
          targetId: targetId,
          targetType: targetType,
          specificSection: specificSection,
        ),
      ),
    );
  }

  @override
  State<FeedbackSheet> createState() => _FeedbackSheetState();
}

class _FeedbackSheetState extends State<FeedbackSheet> {
  FeedbackCategory _selectedCategory = FeedbackCategory.overall;
  int _rating = 0;
  final _commentController = TextEditingController();

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  bool get _canSubmit => _rating > 0;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return BlocConsumer<FeedbackCubit, FeedbackState>(
      listener: (context, state) {
        if (state.status.isSuccess) {
          Navigator.of(context).pop();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('მადლობა უკუკავშირისთვის!', style: uiTextStyles.bodyBold14),
              backgroundColor: uiColors.successColor,
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 2),
            ),
          );
        }
        if (state.status.isFailed) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('შეცდომა. სცადეთ თავიდან.', style: uiTextStyles.bodyBold14),
              backgroundColor: uiColors.errorColor,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      },
      builder: (context, state) {
        return Container(
          decoration: BoxDecoration(
            color: uiColors.backgroundPrimaryColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 16,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
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
              const SizedBox(height: 16),

              // Title
              Text(
                'შეფასება',
                style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
              ),
              const SizedBox(height: 4),
              Text(
                'შეაფასეთ AI-ის მიერ გენერირებული ანალიზი',
                style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
              ),
              const SizedBox(height: 20),

              // Category chips
              Text(
                'კატეგორია',
                style: uiTextStyles.labelBold14.copyWith(color: uiColors.primaryTextColor),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: FeedbackCategory.values.map((cat) {
                  final isSelected = cat == _selectedCategory;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedCategory = cat),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? uiColors.accentColor.withValues(alpha: 0.15)
                            : uiColors.backgroundSecondaryColor,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: isSelected ? uiColors.accentColor : Colors.transparent,
                        ),
                      ),
                      child: Text(
                        cat.displayNameKa,
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
                'რეიტინგი',
                style: uiTextStyles.labelBold14.copyWith(color: uiColors.primaryTextColor),
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
                        starIndex <= _rating ? Icons.star_rounded : Icons.star_outline_rounded,
                        size: 36,
                        color: starIndex <= _rating ? uiColors.warningColor : uiColors.secondaryTextColor,
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 20),

              // Comment field
              Text(
                'კომენტარი (არასავალდებულო)',
                style: uiTextStyles.labelBold14.copyWith(color: uiColors.primaryTextColor),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _commentController,
                maxLines: 3,
                maxLength: 2000,
                decoration: InputDecoration(
                  hintText: 'დაწერეთ თქვენი კომენტარი...',
                  hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
                  filled: true,
                  fillColor: uiColors.backgroundSecondaryColor,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.all(12),
                  counterStyle: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                ),
                style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
              ),
              const SizedBox(height: 20),

              // Submit button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _canSubmit && !state.status.isLoading ? _submit : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: uiColors.accentColor,
                    disabledBackgroundColor: uiColors.accentColor.withValues(alpha: 0.3),
                    foregroundColor: uiColors.backgroundPrimaryColor,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: state.status.isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : Text('გაგზავნა', style: uiTextStyles.bodyBold14),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _submit() {
    final comment = _commentController.text.trim();
    context.read<FeedbackCubit>().submitFeedback(
          FeedbackSubmitRequestParameters(
            targetType: widget.targetType,
            targetId: widget.targetId,
            category: _selectedCategory,
            rating: _rating,
            comment: comment.isEmpty ? null : comment,
            specificSection: widget.specificSection,
          ),
        );
  }
}
