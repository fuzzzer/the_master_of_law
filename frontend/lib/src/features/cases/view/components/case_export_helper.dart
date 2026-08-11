import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

/// Generates and exports a structured case summary.
class CaseExportHelper {
  CaseExportHelper._();

  static void exportToClipboard(BuildContext context, CaseData caseData) {
    final buffer = StringBuffer()
      ..writeln('═══════════════════════════════════')
      ..writeln('კანონის ოსტატი — საქმის რეზიუმე')
      ..writeln('═══════════════════════════════════')
      ..writeln()
      ..writeln('📁 ${caseData.title}')
      ..writeln('⚖️ ${caseData.domain.displayNameKa}')
      ..writeln('📊 სიძლიერის ქულა: ${caseData.strengthScore}/100')
      ..writeln('📅 შექმნილი: ${_fmt(caseData.createdAt)}')
      ..writeln();

    // Facts
    if (caseData.facts.isNotEmpty) {
      buffer.writeln('━━━ ფაქტები (${caseData.facts.length}) ━━━');
      for (final fc in FactClassification.values) {
        final group = caseData.facts.where((f) => f.classificationIndex == fc.index).toList();
        if (group.isNotEmpty) {
          buffer.writeln('\n${fc.emoji} ${fc.displayNameKa}:');
          for (final f in group) {
            buffer.writeln('  • ${f.text}');
          }
        }
      }
      buffer.writeln();
    }

    // Arguments
    if (caseData.arguments.isNotEmpty) {
      buffer.writeln('━━━ არგუმენტები (${caseData.arguments.length}) ━━━');
      for (var i = 0; i < caseData.arguments.length; i++) {
        final arg = caseData.arguments[i];
        buffer
          ..writeln('#${i + 1} ${arg.title} [${arg.strength.displayNameKa}]')
          ..writeln('   ${arg.explanation}');
      }
      buffer.writeln();
    }

    // Strategy
    if (caseData.strategy != null) {
      buffer
        ..writeln('━━━ სტრატეგია ━━━')
        ..writeln('ძირითადი: ${caseData.strategy!.primaryStrategy}');
      if (caseData.strategy!.backupStrategy != null) {
        buffer.writeln('სარეზერვო: ${caseData.strategy!.backupStrategy}');
      }
      buffer.writeln();
    }

    // Evidence
    if (caseData.evidence.isNotEmpty) {
      buffer.writeln('━━━ მტკიცებულებები (${caseData.evidence.length}) ━━━');
      for (final ev in caseData.evidence) {
        buffer.writeln('  📎 ${ev.title} (${ev.type.displayNameKa})');
      }
      buffer.writeln();
    }

    // Timeline
    if (caseData.timeline.isNotEmpty) {
      buffer.writeln('━━━ ვადები ━━━');
      for (final ev in caseData.timeline) {
        buffer.writeln('  ${ev.type.icon} ${_fmt(ev.date)} — ${ev.title}');
      }
      buffer.writeln();
    }

    // Risks
    if (caseData.risks.isNotEmpty) {
      buffer.writeln('━━━ რისკები (${caseData.risks.length}) ━━━');
      for (final r in caseData.risks) {
        buffer.writeln('  ⚠️ [${r.severity.displayNameKa}] ${r.description}');
        if (r.mitigationSuggestion != null) {
          buffer.writeln('     💡 ${r.mitigationSuggestion}');
        }
      }
      buffer.writeln();
    }

    // Action items
    if (caseData.actionItems.isNotEmpty) {
      buffer.writeln('━━━ სამოქმედო გეგმა ━━━');
      for (final item in caseData.actionItems) {
        final check = item.isCompleted ? '☑' : '☐';
        buffer.writeln('  $check ${item.task}');
      }
      buffer.writeln();
    }

    buffer
      ..writeln('═══════════════════════════════════')
      ..writeln('გენერირებულია: კანონის ოსტატი')
      ..writeln(_fmt(DateTime.now()));

    Clipboard.setData(ClipboardData(text: buffer.toString()));

    final colors = context.fuzzzyColors;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        // `FuzzzyToast`'s shape: a `raised` sheet with the semantic colour
        // carried by the CONTENT. The fork filled the whole bar with
        // `successColor` and left the label on Material's default foreground —
        // and the kit ships no `onSuccess` role to fix that with (JOURNAL M5).
        content: Text(
          'საქმე კოპირებულია ბუფერში',
          style: context.fuzzzyTextStyles.body.copyWith(color: colors.success),
        ),
        backgroundColor: colors.raised,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(context.fuzzzyRadius.m),
        ),
      ),
    );
  }

  static String _fmt(DateTime d) => '${d.day}.${d.month.toString().padLeft(2, '0')}.${d.year}';
}
