import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:themasteroflaw/src/src.dart';

class AdminPanelFloatingHead extends StatefulWidget {
  const AdminPanelFloatingHead({super.key, required this.child});

  final Widget child;

  @override
  State<AdminPanelFloatingHead> createState() => _AdminPanelFloatingHeadState();
}

class _AdminPanelFloatingHeadState extends State<AdminPanelFloatingHead> {
  bool _isAdmin = false;
  String _adminKey = '';

  @override
  void initState() {
    super.initState();
    _checkAdminStatus();
  }

  Future<void> _checkAdminStatus() async {
    try {
      final secureStorage = sl.get<SecureStorageService>();
      final key = await secureStorage.getData('temporary_api_key');
      
      if (key == null || key.isEmpty) return;

      final publicClient = sl.get<ThemasteroflawPublicHttpClient>();
      
      final response = await publicClient.get(
        Uri.parse('http://127.0.0.1:8000/api/v1/api-keys/check'),
        options: Options(headers: {'X-Admin-Key': key}),
      );

      if (response.statusCode == 200 && mounted) {
        setState(() {
          _isAdmin = true;
          _adminKey = key;
        });
      }
    } catch (e) {
      // Not an admin or backend is unreachable
      logger.i('Not an admin or backend error: $e');
    }
  }

  Future<void> _generateApiKey() async {
    try {
      final publicClient = sl.get<ThemasteroflawPublicHttpClient>();
      final response = await publicClient.post(
        Uri.parse('http://127.0.0.1:8000/api/v1/api-keys'),
        options: Options(headers: {'X-Admin-Key': _adminKey}),
      );

      if (response.statusCode == 200) {
        final newKey = response.data['api_key'] as String;
        if (mounted) {
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('New API Key'),
              content: SelectableText(newKey),
              actions: [
                TextButton(
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: newKey));
                    Navigator.of(ctx).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Copied to clipboard')),
                    );
                  },
                  child: const Text('Copy & Close'),
                ),
              ],
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to generate key: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isAdmin) return widget.child;

    return Stack(
      children: [
        widget.child,
        Positioned(
          bottom: 100,
          right: 16,
          child: Material(
            color: Colors.transparent,
            child: FloatingActionButton(
              backgroundColor: Colors.purple,
              heroTag: 'admin_panel',
              onPressed: _generateApiKey,
              child: const Icon(Icons.admin_panel_settings, color: Colors.white),
            ),
          ),
        ),
      ],
    );
  }
}
