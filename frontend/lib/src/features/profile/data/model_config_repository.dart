import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:fuzzzy_law/src/src.dart';

/// One model tier as the backend reports it.
class TierModel {
  /// Which model is actually serving this tier right now.
  final String model;

  /// `personal` — this user's own choice; `override` — the admin default for
  /// the deployment; `env` — what it was deployed with.
  /// Shown to the reader because "the app is on X" and "someone changed it
  /// to X" are different facts and only one of them survives a reset.
  final String source;

  const TierModel({required this.model, required this.source});

  /// True when this tier is NOT simply what the app was deployed with —
  /// either this user chose it, or an admin changed the default.
  ///
  /// Both call sites ask the same question ("is there something to undo?"),
  /// so a personal choice has to count. Matching only 'override' hid the
  /// reset button from the very user who had just picked a model.
  bool get isOverride => source != 'env';

  /// This user's own choice, as opposed to the deployment's default.
  bool get isPersonal => source == 'personal';

  factory TierModel.fromMap(Map<String, dynamic> m) => TierModel(
    model: m['model']?.toString() ?? '',
    source: m['source']?.toString() ?? 'env',
  );
}

class ModelConfig {
  final TierModel strong;
  final TierModel cheap;
  final List<String> available;

  /// The backend decides this, not the client. Under bring-your-own-key it is
  /// true for everyone, because the choice only affects the caller who made
  /// it. It goes false only in a deployment where the operator pays for the
  /// AI, and a model change would spend their money on everyone's behalf.
  final bool canEdit;

  const ModelConfig({
    required this.strong,
    required this.cheap,
    required this.available,
    required this.canEdit,
  });

  factory ModelConfig.fromMap(Map<String, dynamic> m) => ModelConfig(
    strong: TierModel.fromMap(
      Map<String, dynamic>.from(m['strong'] as Map? ?? const {}),
    ),
    cheap: TierModel.fromMap(
      Map<String, dynamic>.from(m['cheap'] as Map? ?? const {}),
    ),
    available: (m['available'] as List<dynamic>? ?? const [])
        .map((e) => e.toString())
        .toList(),
    canEdit: m['can_edit'] == true,
  );
}

class ModelConfigRepository {
  final FuzzzyLawHttpClient _httpClient;

  ModelConfigRepository() : _httpClient = sl.get<FuzzzyLawHttpClient>();

  Uri get _uri => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}/api/v1/models',
  );

  Future<ModelConfig> fetch() async {
    final r = await _httpClient.get<Map<String, dynamic>>(_uri);
    return ModelConfig.fromMap(r.data!);
  }

  /// Changing a tier costs a round-trip AND a smoke test on the server, so it
  /// is slower than a normal PUT — the caller must keep its pending state up
  /// until this returns.
  Future<ModelConfig> setModels({String? strong, String? cheap}) async {
    final r = await _httpClient.put<Map<String, dynamic>>(
      _uri,
      body: {
        if (strong != null) 'strong': strong,
        if (cheap != null) 'cheap': cheap,
      },
      options: longRunningRequest(),
    );
    return ModelConfig.fromMap(r.data!);
  }

  Future<ModelConfig> reset() async {
    final r = await _httpClient.delete<Map<String, dynamic>>(_uri);
    return ModelConfig.fromMap(r.data!);
  }
}
