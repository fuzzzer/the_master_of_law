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



  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final key = _controller.text.trim();
    if (key.isEmpty) return;

    setState(() => _isLoading = true);
    try {
      final secureStorage = sl.get<SecureStorageService>();
      await secureStorage.saveData('temporary_api_key', key);
      
      if (mounted) {
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
