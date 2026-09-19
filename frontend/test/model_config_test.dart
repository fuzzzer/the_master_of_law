import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/features/profile/profile.dart';

void main() {
  group('ModelConfig parsing', () {
    test('reads both tiers and their source', () {
      final c = ModelConfig.fromMap(const {
        'strong': {'model': 'gemini-3.5-flash', 'source': 'override'},
        'cheap': {'model': 'gemini-3.7-flash', 'source': 'env'},
        'available': ['gemini-3.5-flash', 'gemini-3.7-flash'],
        'can_edit': true,
      });
      expect(c.strong.model, 'gemini-3.5-flash');
      expect(c.strong.isOverride, isTrue);
      expect(c.cheap.isOverride, isFalse,
          reason: 'an env tier is not an override — the reset button keys off this');
      expect(c.available, hasLength(2));
      expect(c.canEdit, isTrue);
    });

    test('a response missing fields does not throw', () {
      // The settings screen is additive: a partial or unexpected response
      // must degrade to a quiet row, never take the whole page down.
      final c = ModelConfig.fromMap(const {});
      expect(c.strong.model, '');
      expect(c.available, isEmpty);
      expect(c.canEdit, isFalse);
    });

    test('can_edit defaults to false rather than true', () {
      // Failing OPEN here would show an editable control to a user whose PUT
      // the server will reject — an affordance that lies.
      final c = ModelConfig.fromMap(const {
        'strong': {'model': 'x', 'source': 'env'},
        'cheap': {'model': 'y', 'source': 'env'},
      });
      expect(c.canEdit, isFalse);
    });
  });

  group('ModelConfigState', () {
    test('is busy while a tier change is in flight', () {
      const s = ModelConfigState(pendingTier: 'strong');
      expect(s.isBusy, isTrue);
    });

    test('clearPending actually clears', () {
      const s = ModelConfigState(pendingTier: 'strong');
      expect(s.copyWith(clearPending: true).isBusy, isFalse);
    });

    test('an error does not wipe the config already on screen', () {
      // The old value is still the true one — the server rejected the change.
      final s = ModelConfigState(
        config: ModelConfig.fromMap(const {
          'strong': {'model': 'x', 'source': 'env'},
          'cheap': {'model': 'y', 'source': 'env'},
          'available': ['x', 'y'],
          'can_edit': true,
        }),
      ).copyWith(error: 'უცნობი მოდელი', clearPending: true);
      expect(s.error, isNotNull);
      expect(s.config, isNotNull);
      expect(s.config!.strong.model, 'x');
    });
  });
}
