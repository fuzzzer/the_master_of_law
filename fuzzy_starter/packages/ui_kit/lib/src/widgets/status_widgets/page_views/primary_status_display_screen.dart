import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryStatusScreenDisplay extends StatelessWidget {
  const PrimaryStatusScreenDisplay({
    super.key,
    this.type = UiKitProcessStatusType.custom,
    required this.statusWidget,
    this.messageSpans = const [],
    this.eachMessageSpanPadding = const EdgeInsets.only(
      bottom: 12,
    ),
    required this.actions,
    this.eachBottomActionPadding = const EdgeInsets.only(
      bottom: 12,
    ),
    this.backgroundColor,
  });

  final UiKitProcessStatusType type;
  final Widget statusWidget;
  final List<Widget> messageSpans;
  final EdgeInsets eachMessageSpanPadding;

  final List<Widget> actions;
  final EdgeInsets eachBottomActionPadding;
  final Color? backgroundColor;

  @override
  Widget build(BuildContext context) {
    return PrimaryScaffold(
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SizedBox(
              width: constraints.maxWidth,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const Spacer(),
                  statusWidget,
                  const SizedBox(height: 24),
                  ...messageSpans.map<Widget>(
                    (span) => Padding(
                      padding: eachMessageSpanPadding,
                      child: span,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ...actions.map(
                    (bottomAction) => Padding(
                      padding: eachBottomActionPadding,
                      child: bottomAction,
                    ),
                  ),
                  const Spacer(),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
