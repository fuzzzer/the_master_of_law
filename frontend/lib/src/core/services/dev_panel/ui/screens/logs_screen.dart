import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

class LogsScreen extends StatelessWidget {
  const LogsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    if (kIsWeb) {
      return Scaffold(
        backgroundColor: uiColors.backgroundPrimaryColor,
        body: Center(
          child: Text(
            'Logs not available on web',
            style: TextStyle(color: uiColors.primaryColor),
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
        backgroundColor: uiColors.backgroundPrimaryColor,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
            child: BlocBuilder<LogReaderCubit, LogReaderState>(
              builder: (context, state) {
                return StatusBuilder.buildByStatus(
                  status: state.status,
                  onInitial: () => const Center(child: CircularProgressIndicator()),
                  onLoading: () => const Center(child: CircularProgressIndicator()),

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
    final uiColors = Theme.of(context).extension<UiColors>()!;
    final filtered = _query.isEmpty
        ? widget.logs
        : widget.logs.where((e) => e.toLowerCase().contains(_query.toLowerCase())).toList();

    return Column(
      children: [
        TextField(
          controller: _searchController,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
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
                    child: InkWell(
                      onLongPress: () {
                        final scaffoldMessenger = ScaffoldMessenger.of(context);
                        Clipboard.setData(ClipboardData(text: logRecord)).then((_) {
                          scaffoldMessenger.showSnackBar(
                            const SnackBar(
                              content: Text('Copied to the clipboard'),
                            ),
                          );
                        });
                      },
                      child: SelectableText(
                        logRecord,
                        style: TextStyle(color: uiColors.primaryColor),
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
