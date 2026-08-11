import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:themasteroflaw/src/src.dart';

class ApiKeyPromptPage extends StatefulWidget {
  const ApiKeyPromptPage({super.key});

  @override
  State<ApiKeyPromptPage> createState() => _ApiKeyPromptPageState();
}

class _ApiKeyPromptPageState extends State<ApiKeyPromptPage> {
  final _controller = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final key = _controller.text.trim();
    if (key.isEmpty) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final secureStorage = sl.get<SecureStorageService>();
    try {
      // Persist first so the auth interceptor attaches the key, then validate
      // with a lightweight authenticated ping. This avoids persisting a typo'd
      // key that would make every subsequent request 401.
      await secureStorage.saveData('temporary_api_key', key);

      final repository = CreditsRepository(
        remoteDataSource: CreditsRemoteDataSource(),
      );
      final result = await repository.getCredits();

      if (!mounted) return;

      switch (result) {
        // notFound = endpoint missing but key accepted; treat as valid so we
        // don't block access if the credits endpoint isn't deployed yet.
        case CreditsSuccess<int>():
        case CreditsFailure<int>(type: CreditsFailureType.notFound):
          context.go('/cases');
        case CreditsFailure<int>(type: CreditsFailureType.unauthorized):
          await secureStorage.deleteData('temporary_api_key');
          if (mounted) {
            setState(
              () => _error = 'არასწორი გასაღები. შეამოწმეთ და სცადეთ ხელახლა.',
            );
          }
        case CreditsFailure<int>(type: CreditsFailureType.network):
          if (mounted) {
            setState(() => _error = 'სერვერთან დაკავშირება ვერ მოხერხდა.');
          }
        case CreditsFailure<int>():
          // Other server-side errors: accept the key (server reachable, key
          // attached) and let downstream screens surface specifics.
          context.go('/cases');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Scaffold(
      appBar: AppBar(title: const Text('Staging Access')),
      body: Padding(
        padding: density.screen,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Enter your Staging API Key',
              // Was `TextStyle(fontSize: 24, fontWeight: bold)` — a BLOCKING
              // literal size AND a hand-rolled weight. A brand pack owns the
              // type scale; 24/bold is `titleM`, the role every other page
              // header in this app took at M3–M9b.
              style: type.titleM.copyWith(color: colors.ink),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xxl),
            TextField(
              controller: _controller,
              style: type.body.copyWith(color: colors.fieldText),
              // The local `OutlineInputBorder()` is deleted: fill, all five
              // border states, radius, content padding and hint style come
              // from M1's inputDecorationTheme (RUN_BRIEF §4). The fork's bare
              // outline was the ONE field in the app that opted out.
              decoration: const InputDecoration(hintText: 'sk_...'),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _submit(),
            ),
            if (_error != null) ...[
              SizedBox(height: space.m),
              Text(
                _error!,
                // `Colors.red` → `destructiveText`, the legible red. This is
                // the screen's only red and it is duty 4's idle text form.
                style: type.body.copyWith(color: colors.destructiveText),
                textAlign: TextAlign.center,
              ),
            ],
            SizedBox(height: space.xxl),
            SizedBox(
              width: double.infinity,
              // Dimension: the full-width CTA height. 50 → the 48 every other
              // full-width CTA in this app uses (M8's add-fact button).
              height: 48,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.actionPrimaryBg,
                  foregroundColor: colors.actionPrimaryFg,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                ),
                // Was `TextStyle(fontSize: 16)` — the second BLOCKING literal.
                // A button label is `control`, always.
                child: Text('Access Application', style: type.control),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
