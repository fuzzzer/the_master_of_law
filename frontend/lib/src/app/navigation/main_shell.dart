import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';

/// Main app shell with 4-tab bottom navigation.
/// Tabs: საქმეები (Cases), ჩატი (Chat), კანონები (Laws), პროფილი (Profile)
class MainShell extends StatelessWidget {
  const MainShell({
    super.key,
    required this.navigationShell,
  });

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    // The nav bar's own top rule is a `line`, read straight from the roles.
    // The fork derived it as `bottomNavigationBarTheme.unselectedItemColor` at
    // alpha 0.12 with a `Colors.white12` fallback — three problems in one
    // expression: an alpha tint of a FOREGROUND role (USING §2.4), a Material
    // sub-theme read standing in for a role, and a hardcoded Material colour
    // that only ever looked right on a dark skin. `line` IS this hairline.
    final colors = context.fuzzzyColors;

    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: colors.line)),
        ),
        child: BottomNavigationBar(
          currentIndex: navigationShell.currentIndex,
          onTap: (index) => navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          ),
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.folder_special_outlined),
              activeIcon: Icon(Icons.folder_special),
              label: 'საქმეები',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.chat_outlined),
              activeIcon: Icon(Icons.chat),
              label: 'ჩატი',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.menu_book_outlined),
              activeIcon: Icon(Icons.menu_book),
              label: 'კანონები',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: 'პროფილი',
            ),
          ],
        ),
      ),
    );
  }
}
