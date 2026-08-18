import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';

/// In-memory stand-in — the real one is a platform channel.
class _FakeSecureStorage extends SecureStorageService {
  _FakeSecureStorage() : super(const FlutterSecureStorage());

  final Map<String, String> store = {};
  int reads = 0;

  @override
  Future<String?> getData(String key) async {
    reads++;
    return store[key];
  }

  @override
  Future<void> saveData(String key, String value) async {
    store[key] = value;
  }

  @override
  Future<void> deleteData(String key) async {
    store.remove(key);
  }
}

void main() {
  test('the id survives a restart', () async {
    // The property that matters: this id is the only thing tying a user to
    // their cases. If it changed on relaunch, every user would silently lose
    // everything they had built.
    final storage = _FakeSecureStorage();

    final first = await DeviceIdService(storage).get();
    final afterRestart = await DeviceIdService(storage).get();

    expect(afterRestart, first);
  });

  test('two installs never collide', () async {
    final a = await DeviceIdService(_FakeSecureStorage()).get();
    final b = await DeviceIdService(_FakeSecureStorage()).get();

    expect(a, isNot(b));
  });

  test('it is not read from storage on every request', () async {
    // Read on every outgoing call; a platform-channel round trip per request
    // would show up as latency on the whole app.
    final storage = _FakeSecureStorage();
    final service = DeviceIdService(storage);

    await service.get();
    final readsAfterFirst = storage.reads;
    await service.get();
    await service.get();

    expect(storage.reads, readsAfterFirst);
  });

  test('it is long and hex — not guessable', () async {
    // Anyone holding another install's id can read that install's cases, so a
    // short or predictable id would be an enumeration hole.
    final id = await DeviceIdService(_FakeSecureStorage()).get();

    expect(id.length, 32);
    expect(RegExp(r'^[0-9a-f]{32}$').hasMatch(id), isTrue);
  });
}
