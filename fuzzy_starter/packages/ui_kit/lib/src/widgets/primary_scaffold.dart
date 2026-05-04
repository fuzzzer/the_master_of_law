import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryScaffold extends StatelessWidget {
  const PrimaryScaffold({
    super.key,
    required this.body,
    this.appBar,
    this.bottomNavigationBar,
    this.scaffoldKey,
    this.floatingActionButton,
    this.floatingActionButtonLocation,
    this.resizeToAvoidBottomInset,
    this.hasSafeAreaOnTop = true,
    this.hasSafeAreaOnBottom = true,
    this.backgroundColor,
    this.actionsRow,
    this.hasAutomaticBackButton = true,
    this.drawer,
  });

  final PreferredSizeWidget? appBar;
  final Widget? bottomNavigationBar;
  final Widget body;
  final Widget? floatingActionButton;
  final FloatingActionButtonLocation? floatingActionButtonLocation;
  final Key? scaffoldKey;
  final bool? resizeToAvoidBottomInset;
  final bool hasSafeAreaOnTop;
  final bool hasSafeAreaOnBottom;
  final Color? backgroundColor;
  final Widget? actionsRow;
  final bool hasAutomaticBackButton;
  final Widget? drawer;

  @override
  Widget build(BuildContext context) {
    final uiColors = Theme.of(context).extension<UiColors>()!;

    return Scaffold(
      key: scaffoldKey,
      appBar: appBar,
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: backgroundColor ?? uiColors.backgroundPrimaryColor,
      drawer: drawer,
      body: GestureDetector(
        onTap: () {
          FocusScope.of(context).unfocus();
        },
        child: Stack(
          children: [
            SafeArea(
              top: hasSafeAreaOnTop,
              bottom: hasSafeAreaOnBottom,
              child: body,
            ),
            if (hasAutomaticBackButton || actionsRow != null)
              Align(
                alignment: Alignment.bottomCenter,
                child: Padding(padding: const EdgeInsets.only(left: 16, right: 16, bottom: 16), child: actionsRow),
              ),
          ],
        ),
      ),
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: bottomNavigationBar,
    );
  }
}
