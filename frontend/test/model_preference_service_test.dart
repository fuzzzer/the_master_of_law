import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';

class _FakeSecureStorage extends SecureStorageService {
  _FakeSecureStorage() : super(const FlutterSecureStorage());

  final Map<String, String> store = {};

  @override
  Future<String?> getData(String key) async => store[key];

  @override
  Future<void> saveData(String key, String value) async => store[key] = value;

  @override
  Future<void> deleteData(String key) async => store.remove(key);
}

void main() {
  test('a choice survives a restart', () async {
    final storage = _FakeSecureStorage();
    await (ModelPreferenceService(storage)..load()).save(strong: 'model-x');

    final afterRestart = ModelPreferenceService(storage);
    await afterRestart.load();

    expect(afterRestart.strong, 'model-x');
  });

  test('saving one tier leaves the other alone', () async {
    final s = ModelPreferenceService(_FakeSecureStorage());
    await s.load();
    await s.save(strong: 'a', cheap: 'b');
    await s.save(strong: 'c');

    expect(s.strong, 'c');
    expect(s.cheap, 'b');
  });

  test('no selection means no headers and no query params', () async {
    // The absence of a choice must send nothing at all, so the server falls
    // through to its own default rather than being pinned to an empty string.
    final s = ModelPreferenceService(_FakeSecureStorage());
    await s.load();

    expect(s.hasSelection, isFalse);
    expect(s.queryParameters, isEmpty);
  });

  test('clear drops both tiers from storage, not just memory', () async {
    final storage = _FakeSecureStorage();
    final s = ModelPreferenceService(storage);
    await s.load();
    await s.save(strong: 'a', cheap: 'b');
    await s.clear();

    expect(s.hasSelection, isFalse);
    expect(storage.store, isEmpty);

    final reloaded = ModelPreferenceService(storage);
    await reloaded.load();
    expect(reloaded.hasSelection, isFalse);
  });

  test('websocket query params carry the selection', () async {
    // Browsers cannot set headers on a WebSocket handshake, so the chat
    // stream — the heaviest consumer of the model — depends on these.
    final s = ModelPreferenceService(_FakeSecureStorage());
    await s.load();
    await s.save(strong: 'a', cheap: 'b');

    expect(s.queryParameters, {'model_strong': 'a', 'model_cheap': 'b'});
  });

  test('an empty stored value is treated as no choice', () async {
    final storage = _FakeSecureStorage();
    storage.store[ModelPreferenceService.strongKey] = '';
    final s = ModelPreferenceService(storage);
    await s.load();

    expect(s.strong, isNull);
    expect(s.queryParameters, isEmpty);
  });
}
