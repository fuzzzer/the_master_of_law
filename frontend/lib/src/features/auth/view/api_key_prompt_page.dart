import 'package:flutter/material.dart';
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

      final repository = CreditsRepository(remoteDataSource: CreditsRemoteDataSource());
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
            setState(() => _error = 'არასწორი გასაღები. შეამოწმეთ და სცადეთ ხელახლა.');
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
    return Scaffold(
      appBar: AppBar(title: const Text('Staging Access')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Enter your Staging API Key',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                hintText: 'sk_...',
                border: OutlineInputBorder(),
              ),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _submit(),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(
                _error!,
                style: const TextStyle(color: Colors.red),
                textAlign: TextAlign.center,
              ),
            ],
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: const Text('Access Application', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
