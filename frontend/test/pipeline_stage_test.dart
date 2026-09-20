import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/features/consultation/bloc/bloc.dart';

void main() {
  group('PipelineStage', () {
    test('parses a backend stage frame', () {
      final s = PipelineStage.fromMap(const {
        'type': 'stage',
        'key': 'verify',
        'label': 'მუხლების გადამოწმება',
        'detail': '5 მუხლი მოწმდება',
        'index': 7,
        'total': 10,
      });
      expect(s.key, 'verify');
      expect(s.label, 'მუხლების გადამოწმება');
      expect(s.detail, '5 მუხლი მოწმდება');
      expect(s.index, 7);
    });

    test('survives a frame with fields missing', () {
      final s = PipelineStage.fromMap(const {'key': 'draft'});
      expect(s.key, 'draft');
      expect(s.detail, isNull);
      expect(s.progress, 0);
    });

    test('progress spans 0..1 across the declared stages', () {
      expect(const PipelineStage(key: 'a', label: '', index: 0, total: 10).progress, 0);
      expect(const PipelineStage(key: 'z', label: '', index: 9, total: 10).progress, 1);
      expect(const PipelineStage(key: 'm', label: '', index: 9, total: 10).progress,
          lessThanOrEqualTo(1.0));
    });

    test('equality tracks detail, so a same-stage detail update repaints', () {
      const a = PipelineStage(key: 'rank', label: 'x', index: 3, total: 10);
      const b = PipelineStage(
          key: 'rank', label: 'x', index: 3, total: 10, detail: 'ნაპოვნია 23 მუხლი');
      expect(a == b, isFalse);
    });
  });

  group('ConsultationState stage transitions', () {
    // REGRESSION PIN. The cubit sets a stage while clearing the legacy coarse
    // status in ONE copyWith. A `clearStage: true` added to that same call —
    // which is exactly what a blanket edit across the other clear sites
    // produced — makes copyWith null the stage it is being handed, and the
    // indicator shows bare dots for the whole request while the backend is
    // faithfully streaming all ten stages. Wire-level and service-level tests
    // both stayed green through that; only the running UI showed it.
    test('setting a stage while clearing the legacy status keeps the stage', () {
      const stage = PipelineStage(key: 'draft', label: 'პასუხის მომზადება', index: 5, total: 10);
      final s = const ConsultationState(streamingStatus: 'old')
          .copyWith(stage: stage, clearStreamingStatus: true);
      expect(s.stage, isNotNull, reason: 'the stage must survive its own copyWith');
      expect(s.stage!.key, 'draft');
      expect(s.streamingStatus, isNull);
    });

    test('clearing the stage on completion actually clears it', () {
      const stage = PipelineStage(key: 'polish', label: 'x', index: 9, total: 10);
      final s = const ConsultationState(stage: stage).copyWith(clearStage: true);
      expect(s.stage, isNull);
    });

    test('an unrelated copyWith does not drop an in-flight stage', () {
      const stage = PipelineStage(key: 'search', label: 'x', index: 2, total: 10);
      final s = const ConsultationState(stage: stage).copyWith(isSending: true);
      expect(s.stage, same(stage));
    });
  });
}
