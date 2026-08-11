import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

class LogsScreen extends StatelessWidget {
  const LogsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (kIsWeb) {
      return Scaffold(
        body: Center(
          child: Text(
            'Logs not available on web',
            style: context.fuzzzyTextStyles.body.copyWith(
              color: context.fuzzzyColors.ink,
            ),
          ),
        ),
      );
    }

    return BlocProvider(
      create: (context) => LogReaderCubit(
        logStorageService: LogStorageService(
          appStoragePath: sl.get<AppSupportDirectory>().directory.path,
        ),
      )..getLogs(),
      child: Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
            child: BlocBuilder<LogReaderCubit, LogReaderState>(
              builder: (context, state) {
                return StatusBuilder.buildByStatus(
                  status: state.status,
                  onInitial: () =>
                      const Center(child: CircularProgressIndicator()),
                  onLoading: () =>
                      const Center(child: CircularProgressIndicator()),

                  onSuccess: () => _LogsListWithSearch(
                    logs: state.logRecordList!,
                  ),

                  onFailure: () => Text(state.failure!.message ?? ''),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

class _LogsListWithSearch extends StatefulWidget {
  const _LogsListWithSearch({required this.logs});

  final List<String> logs;

  @override
  State<_LogsListWithSearch> createState() => _LogsListWithSearchState();
}

class _LogsListWithSearchState extends State<_LogsListWithSearch> {
  final _searchController = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final filtered = _query.isEmpty
        ? widget.logs
        : widget.logs
              .where((e) => e.toLowerCase().contains(_query.toLowerCase()))
              .toList();

    return Column(
      children: [
        TextField(
          controller: _searchController,
          decoration: const InputDecoration(
            prefixIcon: Icon(Icons.search),
            hintText: 'Search logs…',
          ),
          onChanged: (value) => setState(() => _query = value),
        ),
        const SizedBox(height: 12),

        Expanded(
          child: DevPanelContentList(
            children: filtered.map<Widget>((logRecord) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onLongPress: () {
                        // M11: the messenger-capture + `.then` dance existed
                        // only to survive the async gap. Showing the toast
                        // synchronously (as the app's three other copy sites
                        // already do) removes the gap instead of guarding it.
                        Clipboard.setData(ClipboardData(text: logRecord));
                        FuzzzyToast.show(
                          context,
                          message: 'Copied to the clipboard',
                          kind: FuzzzyToastKind.success,
                          qaId: 'devPanel.logCopied',
                        );
                      },
                      child: SelectableText(
                        logRecord,
                        style: type.data.copyWith(color: colors.ink),
                        textAlign: TextAlign.start,
                      ),
                    ),
                  ),
                  const Divider(),
                ],
              );
            }).toList(),
          ),
        ),
      ],
    );
  }
}
