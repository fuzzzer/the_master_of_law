import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return BlocConsumer<FeedbackCubit, FeedbackState>(
      listener: (context, state) {
        if (state.status.isSuccess) {
          Navigator.of(context).pop();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              // `FuzzzyToast`'s shape: a `raised` sheet with the semantic
              // colour carried by the CONTENT, not as a solid fill. The kit
              // ships no `onSuccess` foreground, and needs none — see
              // JOURNAL M5.
              content: Text(
                'მადლობა უკუკავშირისთვის!',
                style: type.body.copyWith(color: colors.success),
              ),
              backgroundColor: colors.raised,
              behavior: SnackBarBehavior.floating,
              // Dwell time, not animation — see JOURNAL M3.
              duration: const Duration(seconds: 2),
            ),
          );
        }
        if (state.status.isFailed) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'შეცდომა. სცადეთ თავიდან.',
                style: type.body.copyWith(color: colors.destructiveText),
              ),
              backgroundColor: colors.raised,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      },
      builder: (context, state) {
        return Container(
          decoration: BoxDecoration(
            // Rung 2 of the ladder: an overlay is `raised` + `lineStrong`.
            color: colors.raised,
            border: Border(top: BorderSide(color: colors.lineStrong)),
            borderRadius: BorderRadius.vertical(top: Radius.circular(radius.l)),
          ),
          padding: density.dialog.copyWith(
            bottom: density.dialog.bottom + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  // Dimensions, not gaps: the grabber's fixed footprint.
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    // `lineStrong`, not `line`: on a `raised` sheet a `line`
                    // hairline all but disappears, and a grabber is an
                    // affordance, not a divider.
                    color: colors.lineStrong,
                    borderRadius: BorderRadius.circular(radius.s),
                  ),
                ),
              ),
              SizedBox(height: space.l),

              // Title
              Text(
                'შეფასება',
                style: type.titleM.copyWith(color: colors.ink),
              ),
              SizedBox(height: space.xs),
              Text(
                'შეაფასეთ AI-ის მიერ გენერირებული ანალიზი',
                style: type.body.copyWith(color: colors.inkMute),
              ),
              SizedBox(height: space.xl),

              // Category chips
              Text('კატეგორია', style: type.control.copyWith(color: colors.ink)),
              SizedBox(height: space.s),
              Wrap(
                spacing: space.s,
                runSpacing: space.s,
                children: FeedbackCategory.values.map((cat) {
                  final isSelected = cat == _selectedCategory;
                  // `FuzzzyFilterChip`'s exact recipe (inputs/fuzzzy_filter_chip
                  // .dart:92-112): density.chip + radius.s, selection is
                  // INVERTED-MONO, never an accent tint — harvest/mol.md §4.
                  return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => setState(() => _selectedCategory = cat),
                    child: Container(
                      padding: density.chip,
                      decoration: BoxDecoration(
                        color: isSelected
                            ? colors.actionPrimaryBg
                            : colors.surface,
                        borderRadius: BorderRadius.circular(radius.s),
                        border: Border.all(
                          color: isSelected
                              ? colors.actionPrimaryBg
                              : colors.line,
                        ),
                      ),
                      child: Text(
                        cat.displayNameKa,
                        style: type.control.copyWith(
                          color: isSelected
                              ? colors.actionPrimaryFg
                              : colors.inkMute,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
              SizedBox(height: space.xl),

              // Star rating
              Text('რეიტინგი', style: type.control.copyWith(color: colors.ink)),
              SizedBox(height: space.s),
              Row(
                children: List.generate(5, (index) {
                  final starIndex = index + 1;
                  // `FuzzzyRatingStars` (inputs/fuzzzy_rating_stars.dart:55,68):
                  // fill = `ink`, empty = `lineStrong`, MONOCHROME — the fork's
                  // amber star is a red-discipline violation (harvest §1).
                  // The hit region is padded to >=44x44; the glyph stays 36.
                  return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => setState(() => _rating = starIndex),
                    child: Padding(
                      padding: EdgeInsets.only(right: space.xs),
                      child: SizedBox(
                        width: FuzzzyViewport.minTouchTarget,
                        height: FuzzzyViewport.minTouchTarget,
                        child: Icon(
                          starIndex <= _rating
                              ? Icons.star_rounded
                              : Icons.star_outline_rounded,
                          size: 36,
                          color: starIndex <= _rating
                              ? colors.ink
                              : colors.lineStrong,
                        ),
                      ),
                    ),
                  );
                }),
              ),
              SizedBox(height: space.xl),

              // Comment field
              Text(
                'კომენტარი (არასავალდებულო)',
                style: type.control.copyWith(color: colors.ink),
              ),
              SizedBox(height: space.s),
              TextField(
                controller: _commentController,
                maxLines: 3,
                maxLength: 2000,
                // fill / borders / contentPadding / hintStyle all inherited
                // from inputDecorationTheme. Only the counter is declared:
                // the theme has no `counterStyle` slot.
                decoration: InputDecoration(
                  hintText: 'დაწერეთ თქვენი კომენტარი...',
                  counterStyle: type.bodyS.copyWith(color: colors.helper),
                ),
                style: type.body.copyWith(color: colors.fieldText),
              ),
              SizedBox(height: space.xl),

              // Submit button
              // `FuzzzyButton.primary`'s recipe: actionPrimary pair, radius.m,
              // `control` label, and DISABLED IS OPACITY 0.42 over the whole
              // button (buttons/fuzzzy_button.dart:175) rather than a separate
              // faded fill — the kit ships no disabled colour role.
              Opacity(
                opacity: _canSubmit && !state.status.isLoading ? 1.0 : 0.42,
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed:
                        _canSubmit && !state.status.isLoading ? _submit : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colors.actionPrimaryBg,
                      foregroundColor: colors.actionPrimaryFg,
                      disabledBackgroundColor: colors.actionPrimaryBg,
                      disabledForegroundColor: colors.actionPrimaryFg,
                      padding: density.snug,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(radius.m),
                      ),
                    ),
                    child: state.status.isLoading
                        ? SizedBox(
                            // Dimension: the in-button spinner's footprint.
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: colors.actionPrimaryFg,
                            ),
                          )
                        : Text(
                            'გაგზავნა',
                            style: type.control
                                .copyWith(color: colors.actionPrimaryFg),
                          ),
                  ),
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
