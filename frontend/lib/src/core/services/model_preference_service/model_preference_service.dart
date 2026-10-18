import 'package:fuzzzy_law/src/src.dart';

/// The caller's chosen model per tier, kept on the device.
///
/// WHY ON THE DEVICE: under bring-your-own-key the model is not a deployment
/// setting — the user pays for it with their own key, against their own quota,
/// and their key exposes its own list of models. The usual reason to change it
/// is that they personally exhausted one, and that switch must not drag other
/// users along. So the choice lives with the user who made it and travels on
/// their requests, exactly like the key that pays for them.
///
/// The server stores nothing: it validates a choice, and this holds it.
class ModelPreferenceService {
  ModelPreferenceService(this._secureStorage);

  static const String strongKey = 'model_strong';
  static const String cheapKey = 'model_cheap';

  final SecureStorageService _secureStorage;

  String? _strong;
  String? _cheap;
  bool _loaded = false;

  /// Read once at startup so the interceptor never has to await storage on
  /// the request path.
  Future<void> load() async {
    _strong = _nullIfEmpty(await _secureStorage.getData(strongKey));
    _cheap = _nullIfEmpty(await _secureStorage.getData(cheapKey));
    _loaded = true;
  }

  String? get strong => _strong;

  String? get cheap => _cheap;

  bool get isLoaded => _loaded;

  bool get hasSelection => _strong != null || _cheap != null;

  /// Persist a tier the server has already accepted. Null leaves it untouched.
  Future<void> save({String? strong, String? cheap}) async {
    if (strong != null && strong.isNotEmpty) {
      _strong = strong;
      await _secureStorage.saveData(strongKey, strong);
    }
    if (cheap != null && cheap.isNotEmpty) {
      _cheap = cheap;
      await _secureStorage.saveData(cheapKey, cheap);
    }
  }

  /// Fall back to whatever the deployment defaults to.
  Future<void> clear() async {
    _strong = null;
    _cheap = null;
    await _secureStorage.deleteData(strongKey);
    await _secureStorage.deleteData(cheapKey);
  }

  /// Query parameters for the chat WebSocket, which cannot carry headers.
  Map<String, String> get queryParameters => {
    if (_strong != null) 'model_strong': _strong!,
    if (_cheap != null) 'model_cheap': _cheap!,
  };

  static String? _nullIfEmpty(String? v) => (v == null || v.isEmpty) ? null : v;
}
