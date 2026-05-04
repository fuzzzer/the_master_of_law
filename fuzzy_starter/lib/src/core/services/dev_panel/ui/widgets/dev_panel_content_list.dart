import 'package:flutter/material.dart';

class DevPanelContentList extends StatelessWidget {
  const DevPanelContentList({
    super.key,
    required this.children,
  });

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: children.length,
      itemBuilder: (BuildContext context, int index) => children[index],
    );
  }
}
