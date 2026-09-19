import 'dart:math';

import 'package:fuzzzy_law/src/src.dart';

/// The stable per-install identifier that stands in for a user account.
///
/// v1 ships without login, but cases, conversations and messages are still
/// owned by *someone* on the server. This id is that someone. Without it the
/// backend falls back to hashing the caller's IP address, which means every
/// user behind one office router or mobile carrier NAT shares a single pile
/// of legal matters — for this app that is a privacy failure, not a cosmetic
/// one, so the id is generated on first launch and kept from then on.
///
/// It is an identifier, not a credential: it authenticates nothing, and
/// anyone holding it can read that install's cases. Real accounts replace it
/// later; the server keys the user row the same way either way.
class DeviceIdService {
  DeviceIdService(this._secureStorage);

  static const String storageKey = 'device_id';

  final SecureStorageService _secureStorage;

  String? _cached;

  /// Returns the id for this install, creating it on first call.
  ///
  /// Cached in memory because it is read on every single outgoing request and
  /// secure storage is a platform-channel round trip.
  Future<String> get() async {
    final cached = _cached;
    if (cached != null) return cached;

    final stored = await _secureStorage.getData(storageKey);
    if (stored != null && stored.isNotEmpty) {
      _cached = stored;
      return stored;
    }

    final generated = _generate();
    await _secureStorage.saveData(storageKey, generated);
    _cached = generated;
    return generated;
  }

  /// 128 bits from the platform CSPRNG, hex encoded.
  ///
  /// Random.secure() rather than Random(): a guessable id would let anyone
  /// enumerate their way into other people's cases, which is exactly the
  /// exposure this id exists to prevent.
  static String _generate() {
    final rng = Random.secure();
    final bytes = List<int>.generate(16, (_) => rng.nextInt(256));
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }
}
