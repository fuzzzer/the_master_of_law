import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// The monochrome glyph for a timeline event type.
///
/// Replaces `TimelineEventType.icon`, which returns the text glyphs
/// `'✓' / '⏰' / '⭐'`. One of the two call sites rendered them as
/// `Text(icon, style: TextStyle(fontSize: 16))`, and **`fontSize:` is a
/// BLOCKING guard rule that must die in the slice that touches it** — a `Text`
/// with a hardcoded size cannot become a role without becoming an `Icon`
/// (JOURNAL M8 §A). So both call sites take icons and the enum's `icon` getter
/// is left orphaned for M11/M12 to delete with the rest of the dead surface.
IconData _typeIcon(TimelineEventType t) => switch (t) {
  TimelineEventType.past => Icons.check, // ✓
  TimelineEventType.deadline => Icons.schedule, // ⏰
  TimelineEventType.milestone => Icons.star_outline, // ⭐
};

/// The role a timeline event's dot, rule and countdown all take.
///
/// **This is M8 §B's deadline decision, executed on the screen it was written
/// for.** The deadline rung KEEPS its red — a deadline inside a week genuinely
/// is time-critical, and MAPPING §2.6 maps "timeline overdue" to `destructive`.
/// Two things changed from the fork:
///
/// * **The ≥30-day rung was `success` green. "No news" is not good news, it is
///   no news** — a deadline five months out is not an achievement. It drops to
///   the neutral `inkMute`.
/// * **`past` was `success` too.** A past event is *history*, not a win; a
///   signed contract and a lost hearing are both `past`. Also `inkMute`.
///
/// `milestone` takes `ink` — MAPPING §2.2 pre-decided that switch arm at M0.
/// Net effect: **one red voice on the screen** (the imminent deadline), one
/// amber (the approaching one), and everything else monochrome.
Color _eventRole(FuzzzyColors c, TimelineEventData e) => switch (e.type) {
  TimelineEventType.past => c.inkMute,
  TimelineEventType.milestone => c.ink,
  TimelineEventType.deadline =>
    e.daysRemaining < 7
        ? c.destructive
        : e.daysRemaining < 30
        ? c.warning
        : c.inkMute,
};

/// Timeline + deadlines with vertical visualization, countdown display, urgency colors.
class CaseTimelineSection extends StatelessWidget {
  const CaseTimelineSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final events = List<TimelineEventData>.from(caseData.timeline)
      ..sort((a, b) => a.date.compareTo(b.date));

    return Column(
      children: [
        Expanded(
          child: events.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Dimension: the oversized empty-state glyph, `inkFaint`.
                      Icon(Icons.timeline, size: 48, color: colors.inkFaint),
                      SizedBox(height: space.l),
                      Text(
                        'ვადები ჯერ არ არის',
                        style: type.body.copyWith(color: colors.inkMute),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: density.screen,
                  itemCount: events.length,
                  itemBuilder: (context, index) {
                    final event = events[index];
                    final isLast = index == events.length - 1;
                    final role = _eventRole(colors, event);

                    return IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            // Dimension: the rail gutter's fixed width, which
                            // keeps every card's left edge on one line.
                            width: 32,
                            child: Column(
                              children: [
                                Container(
                                  // Dimension: the timeline node. Larger than
                                  // §4.4's 8px status dot on purpose — this one
                                  // is a positional marker on a rail, not a
                                  // status disc inside a chip.
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(
                                    color: role,
                                    // `BoxShape.circle` → radius.circle on a
                                    // provably square box (MAPPING §6).
                                    borderRadius: BorderRadius.circular(
                                      radius.circle,
                                    ),
                                  ),
                                ),
                                if (!isLast)
                                  Expanded(
                                    child: Container(
                                      // Dimension: the connector rail. MAPPING
                                      // §2.7 — a 2px rail painted from
                                      // `surfaceColor` is a `line`, not a
                                      // surface.
                                      width: 2,
                                      color: colors.line,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                          Expanded(
                            child: Padding(
                              padding: EdgeInsets.only(bottom: space.l),
                              // The event's role keeps its 3px leading rule —
                              // the sanctioned home for a semantic colour
                              // (`FuzzzyBanner`'s shape) — and the other three
                              // sides GAIN the `line` hairline the fork never
                              // drew. T-0254: as a per-side `Border` +
                              // `borderRadius` this threw at paint for EVERY
                              // event type (`_eventRole` is never `line`).
                              // Missed by the ticket's original 4-site sweep
                              // and found by the M13b scanner.
                              child: AppRuleCard(
                                rule: role,
                                borderRadius: radius.m,
                                ruleWidth: 3,
                                padding: density.tile,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        // Was `Text(event.type.icon, style:
                                        // TextStyle(fontSize: 16))` — a
                                        // BLOCKING literal. It leads the card's
                                        // `ink` title, so the glyph is `ink`
                                        // (M9 §E).
                                        Icon(
                                          _typeIcon(event.type),
                                          size: 16,
                                          color: colors.ink,
                                        ),
                                        SizedBox(width: space.s),
                                        Expanded(
                                          child: Text(
                                            event.title,
                                            style: type.titleS.copyWith(
                                              color: colors.ink,
                                            ),
                                          ),
                                        ),
                                        if (event.type ==
                                            TimelineEventType.deadline)
                                          Text(
                                            event.daysRemaining > 0
                                                ? '${event.daysRemaining} დღე'
                                                : event.daysRemaining == 0
                                                ? 'დღეს!'
                                                : 'ვადაგადაც.',
                                            // Georgian in every branch, so it
                                            // stays a Georgian-capable role —
                                            // NOT the mono `data` (the M6b/M7
                                            // test is the STRING, not the
                                            // datum).
                                            style: type.control.copyWith(
                                              color: role,
                                            ),
                                          ),
                                      ],
                                    ),
                                    SizedBox(height: space.xs),
                                    Text(
                                      '${event.date.day}.${event.date.month.toString().padLeft(2, '0')}.${event.date.year}',
                                      // Digits and dots only — no Georgian —
                                      // so this date CAN take the mono role,
                                      // and tabular figures are what a column
                                      // of dates wants.
                                      style: type.dataS.copyWith(
                                        color: colors.inkMute,
                                      ),
                                    ),
                                    if (event.description != null &&
                                        event.description!.isNotEmpty) ...[
                                      SizedBox(height: space.xs),
                                      Text(
                                        event.description!,
                                        style: type.body.copyWith(
                                          color: colors.inkMute,
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: density.screen,
          child: SizedBox(
            width: double.infinity,
            // Dimension: the full-width CTA height (M8's add-fact button).
            height: 48,
            child: OutlinedButton.icon(
              onPressed: () => _showAddEvent(context),
              icon: const Icon(Icons.add),
              label: const Text('ახალი ვადა'),
              // `FuzzzyButton.secondary`'s shape (M8 judgement 9).
              style: OutlinedButton.styleFrom(
                foregroundColor: colors.ink,
                side: BorderSide(color: colors.lineStrong),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showAddEvent(BuildContext parentContext) {
    final titleController = TextEditingController();
    var selectedDate = DateTime.now().add(const Duration(days: 7));
    var selectedType = TimelineEventType.deadline;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      // The sheet draws its own `raised` + `lineStrong` box (M5's
      // feedback_sheet idiom), so the route must not paint a second one.
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final colors = ctx.fuzzzyColors;
        final type = ctx.fuzzzyTextStyles;
        final space = ctx.fuzzzySpace;
        final radius = ctx.fuzzzyRadius;
        final density = ctx.fuzzzyDensity;
        final form = ctx.fuzzzyFormStyles;

        return StatefulBuilder(
          builder: (ctx, setState) => Container(
            decoration: BoxDecoration(
              color: colors.raised,
              border: Border(top: BorderSide(color: colors.lineStrong)),
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(radius.l),
              ),
            ),
            padding: density.dialog.copyWith(
              bottom:
                  density.dialog.bottom + MediaQuery.of(ctx).viewInsets.bottom,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ახალი მოვლენა',
                  style: type.titleM.copyWith(color: colors.ink),
                ),
                SizedBox(height: space.l),
                TextField(
                  controller: titleController,
                  style: type.body.copyWith(color: colors.fieldText),
                  decoration: const InputDecoration(hintText: 'სათაური...'),
                ),
                SizedBox(height: space.m),
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: ctx,
                      initialDate: selectedDate,
                      firstDate: DateTime(2020),
                      lastDate: DateTime(2030),
                    );
                    if (picked != null) setState(() => selectedDate = picked);
                  },
                  // A tappable pseudo-field: it takes the FORM roles and
                  // FuzzzyFormStyles geometry, so it is indistinguishable from
                  // the real TextField above it (M6's questionnaire idiom).
                  // The fork gave it a bare `surfaceColor` box with no border
                  // at all, which after M1 would not have matched the field.
                  child: Container(
                    width: double.infinity,
                    padding: form.contentPadding,
                    decoration: BoxDecoration(
                      color: colors.fill,
                      borderRadius: BorderRadius.circular(form.radius),
                      border: Border.all(
                        color: colors.idleBorder,
                        width: form.borderWidth,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.calendar_today,
                          size: 18,
                          color: colors.inkMute,
                        ),
                        SizedBox(width: space.s),
                        Text(
                          '${selectedDate.day}.${selectedDate.month.toString().padLeft(2, '0')}.${selectedDate.year}',
                          // Digits only → the mono role, same as the cards.
                          style: type.dataS.copyWith(color: colors.fieldText),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: space.m),
                Row(
                  children: TimelineEventType.values.map((t) {
                    final isSelected = t == selectedType;
                    return Expanded(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () => setState(() => selectedType = t),
                        child: Container(
                          padding: density.tile,
                          margin: EdgeInsets.symmetric(horizontal: space.xs),
                          // `FuzzzySegmentedControl`'s law: a discrete choice
                          // takes its fill from the ACTION PAIR, and the border
                          // width is CONSTANT across states so the row cannot
                          // reflow on tap (M6's domain-picker fix).
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
                          child: Column(
                            children: [
                              // The `'${t.icon} ${t.displayNameKa}'` string
                              // interpolated the ✓/⏰/⭐ glyphs into the label.
                              // They are now the same monochrome icons the
                              // cards use, so the emoji leave with their twin.
                              Icon(
                                _typeIcon(t),
                                size: 16,
                                color: isSelected
                                    ? colors.actionPrimaryFg
                                    : colors.inkMute,
                              ),
                              SizedBox(height: space.xs),
                              Text(
                                t.displayNameKa,
                                textAlign: TextAlign.center,
                                style: type.control.copyWith(
                                  color: isSelected
                                      ? colors.actionPrimaryFg
                                      : colors.inkMute,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                SizedBox(height: space.l),
                SizedBox(
                  width: double.infinity,
                  // Dimension: the sheet's commit CTA.
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () {
                      if (titleController.text.trim().isEmpty) return;
                      parentContext.read<CaseDetailCubit>().addTimelineEvent(
                        TimelineEventData(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          date: selectedDate,
                          title: titleController.text.trim(),
                          typeIndex: selectedType.index,
                        ),
                      );
                      Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colors.actionPrimaryBg,
                      foregroundColor: colors.actionPrimaryFg,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(radius.m),
                      ),
                    ),
                    // A button label is `control`, always.
                    child: Text('დამატება', style: type.control),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
