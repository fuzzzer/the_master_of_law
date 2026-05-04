import 'package:flutter/material.dart';
import 'package:logger/web.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

void openDevPanel() {
  Navigator.of(navigatorKey.currentContext!).push(
    PageRouteBuilder(
      pageBuilder: (context, animation, secondaryAnimation) => const DevPanelScreen(),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const begin = Offset(0, 1);
        const end = Offset.zero;
        const curve = Curves.easeInOut;

        final tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
        final offsetAnimation = animation.drive(tween);

        return SlideTransition(
          position: offsetAnimation,
          child: child,
        );
      },
      transitionDuration: Durations.medium1,
    ),
  );
}

class DevPanelScreen extends StatelessWidget {
  const DevPanelScreen({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return Scaffold(
      backgroundColor: uiColors.backgroundPrimaryColor,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 32,
          ),
          child: Stack(
            children: [
              DevPanelContentList(
                children: [
                  DevPanelTile(
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (BuildContext context) => const LogsScreen(),
                      ),
                    ),
                    leadingIcon: const Icon(
                      Icons.text_fields,
                      color: Colors.white,
                      size: 46,
                    ),
                    title: 'Logs',
                    subtitle: 'Read Saved Logs',
                  ),
                  ValueListenableBuilder(
                    valueListenable: AppLogger.savingAllLogsWithOutputIntercepting,
                    builder: (context, bool savingAllLogs, _) {
                      return DevPanelTile(
                        leadingIcon: Icon(
                          savingAllLogs ? Icons.all_out : Icons.wifi,
                          color: Colors.white,
                          size: 46,
                        ),
                        title: AppLogger.savingAllLogsWithOutputIntercepting.value
                            ? 'Saving All Logger Logs'
                            : 'Saving Only Request Logs',
                        trailingIcon: ElevatedButton(
                          onPressed: () async {
                            if (AppLogger.savingAllLogsWithOutputIntercepting.value) {
                              logger.initLogSaving(
                                forceInitLogger: true,
                                loggerLevel: AppLogger.loggerLevelThreshold.value,
                              );
                            } else {
                              logger.initLogSaving(
                                savingAllLogs: true,
                                forceInitLogger: true,
                                loggerLevel: AppLogger.loggerLevelThreshold.value,
                              );
                            }
                          },
                          child: const Text(
                            'Toggle',
                          ),
                        ),
                      );
                    },
                  ),
                  ValueListenableBuilder(
                    valueListenable: AppLogger.loggerLevelThreshold,
                    builder: (context, Level logLevel, _) {
                      if (AppLogger.loggerLevelThreshold.value.index == Level.error.index) {
                        return DevPanelTile(
                          leadingIcon: const Icon(
                            Icons.error_outline,
                            color: Colors.white,
                            size: 46,
                          ),
                          title: 'Logger Level: Error',
                          trailingIcon: ElevatedButton(
                            onPressed: () async {
                              logger.initLogSaving(forceInitLogger: true, loggerLevel: Level.debug);
                            },
                            child: const Text(
                              'Toggle',
                            ),
                          ),
                        );
                      } else {
                        return DevPanelTile(
                          leadingIcon: const Icon(
                            Icons.all_inbox,
                            color: Colors.white,
                            size: 46,
                          ),
                          title: AppLogger.loggerLevelThreshold.value.index == Level.debug.index
                              ? 'Logger Level: All'
                              : 'Unknown Log Saving Policy',
                          trailingIcon: ElevatedButton(
                            onPressed: () async {
                              logger.initLogSaving(forceInitLogger: true, loggerLevel: Level.error);
                            },
                            child: const Text(
                              'Toggle',
                            ),
                          ),
                        );
                      }
                    },
                  ),

                  DevPanelTile(
                    leadingIcon: const Icon(
                      Icons.delete,
                      color: Colors.white,
                      size: 46,
                    ),
                    title: 'Clear Logs',
                    trailingIcon: ElevatedButton(
                      onPressed: () async {
                        LogStorageService(
                          appStoragePath: sl.get<AppSupportDirectory>().directory.path,
                        ).clearLogs();
                      },
                      child: const Text(
                        'Clear',
                      ),
                    ),
                  ),
                  DevPanelTile(
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (BuildContext context) => const WorkInProgressFeaturesDisplayScreen(),
                      ),
                    ),
                    leadingIcon: const Icon(
                      Icons.construction,
                      color: Colors.white,
                      size: 46,
                    ),
                    title: 'WIP Features',
                  ),

                  FutureBuilder<PackageInfo>(
                    future: PackageInfo.fromPlatform(),
                    builder: (context, snapshot) {
                      return DevPanelTile(
                        leadingIcon: const Icon(
                          Icons.info_outline,
                          color: Colors.white,
                          size: 46,
                        ),
                        title: 'App Version',
                        subtitle: '${snapshot.data?.version}+${snapshot.data?.buildNumber} ',
                      );
                    },
                  ),
                  const SizedBox(height: 140),
                ],
              ),
              Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.only(
                    bottom: 20,
                    right: 16,
                    left: 16,
                  ),
                  child: PrimaryButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                    },
                    label: 'Go Back',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
