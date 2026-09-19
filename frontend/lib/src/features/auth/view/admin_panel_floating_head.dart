import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

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

      final publicClient = sl.get<FuzzzyLawPublicHttpClient>();

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
      final publicClient = sl.get<FuzzzyLawPublicHttpClient>();
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
                    FuzzzyToast.show(
                      context,
                      message: 'Copied to clipboard',
                      kind: FuzzzyToastKind.success,
                      qaId: 'admin.keyCopied',
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
        FuzzzyToast.show(
          context,
          message: 'Failed to generate key: $e',
          kind: FuzzzyToastKind.error,
          qaId: 'admin.keyFailed',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isAdmin) return widget.child;

    final colors = context.fuzzzyColors;
    final radius = context.fuzzzyRadius;
    final space = context.fuzzzySpace;

    return Stack(
      children: [
        widget.child,
        Positioned(
          // Dimension: clears the bottom nav bar so the head never sits on it.
          bottom: 100,
          right: space.l,
          child: Material(
            // Absence, not colour — the one Material colour the guard allows.
            color: Colors.transparent,
            child: FloatingActionButton(
              // The fork's `Colors.purple` / `Colors.white` was a deliberate
              // "this is the admin build" flag. Ink has no decorative-accent
              // role and MAPPING §2.2 judgement 1 sends emphasis to the action
              // pair, so the head is the same disc `my_cases_page`'s FAB is —
              // it is already gated behind `_isAdmin`, which is what actually
              // makes it an admin affordance.
              backgroundColor: colors.actionPrimaryBg,
              foregroundColor: colors.actionPrimaryFg,
              heroTag: 'admin_panel',
              onPressed: _generateApiKey,
              // Material 3's default FAB is a 16px-rounded square with a
              // shadow; Ink has no shadow vocabulary (M7's FAB call).
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(radius.circle),
              ),
              elevation: 0,
              child: const Icon(Icons.admin_panel_settings),
            ),
          ),
        ),
      ],
    );
  }
}
