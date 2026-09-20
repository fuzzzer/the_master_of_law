import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// What opens when the reader taps a failed turn's bubble.
///
/// Under bring-your-own-key the most common failure is that user's own daily
/// quota on one model being spent, and the way out is a different model, not
/// a wait — so the sheet puts the same picker the profile screen has right
/// under the reason, instead of sending the reader off to find it.
Future<void> showChatErrorSheet(
  BuildContext context, {
  required String message,
}) {
  final colors = context.fuzzzyColors;
  final type = context.fuzzzyTextStyles;
  final space = context.fuzzzySpace;
  final radius = context.fuzzzyRadius;
  final density = context.fuzzzyDensity;

  return showModalBottomSheet<void>(
    context: context,
    backgroundColor: colors.surface,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(radius.l)),
    ),
    isScrollControlled: true,
    builder: (sheetContext) => BlocProvider(
      create: (_) => ModelConfigCubit()..load(),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: density.card,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'პასუხი ვერ მივიღეთ',
                style: type.titleS.copyWith(color: colors.ink),
              ),
              SizedBox(height: space.s),
              Text(message, style: type.body.copyWith(color: colors.ink)),
              SizedBox(height: space.l),
              Text(
                'შეგიძლიათ სცადოთ მოგვიანებით ან აირჩიოთ სხვა მოდელი:',
                style: type.bodyS.copyWith(color: colors.inkMute),
              ),
              SizedBox(height: space.s),
              const ModelSection(),
              SizedBox(height: space.m),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => Navigator.of(sheetContext).pop(),
                  child: const Text('დახურვა'),
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
