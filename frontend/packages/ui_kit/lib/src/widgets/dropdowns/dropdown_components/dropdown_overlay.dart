import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class DropdownOverlay<T> {
  final BuildContext context;
  final List<DropdownItem<T>> items;
  final DropdownItem? selectedItem;
  final LayerLink layerLink;
  final void Function(DropdownItem<T>) onItemSelected;

  OverlayEntry? _overlayEntry;
  late final AnimationController _animationController;

  DropdownOverlay({
    required this.context,
    required this.items,
    required this.selectedItem,
    required this.layerLink,
    required this.onItemSelected,
    required ValueKey<String?> key,
  });

  void show() {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;

    final overlay = Overlay.of(context);
    final RenderBox renderBox = context.findRenderObject() as RenderBox;
    final size = renderBox.size;

    final borderRadius = BorderRadius.circular(16);

    _animationController = AnimationController(vsync: overlay, duration: Durations.medium1);

    _overlayEntry = OverlayEntry(
      builder: (context) {
        return Positioned(
          width: size.width,
          child: CompositedTransformFollower(
            link: layerLink,
            showWhenUnlinked: false,
            offset: Offset(0, size.height + 8),
            child: FadeTransition(
              opacity: CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
              child: Material(
                borderRadius: borderRadius,
                color: uiColors.backgroundSecondaryColor,
                child: ConstrainedBox(
                  constraints: BoxConstraints(maxHeight: 300),
                  child: ListView.builder(
                    padding: EdgeInsets.zero,
                    shrinkWrap: true,
                    itemCount: items.length,
                    itemBuilder: (context, index) {
                      final item = items[index];
                      final bool isSelected = item == selectedItem;

                      return InkWell(
                        borderRadius: borderRadius,
                        onTap: () {
                          onItemSelected(item);
                          remove();
                        },
                        child: Container(
                          decoration: BoxDecoration(
                            color: isSelected ? uiColors.backgroundPrimaryColor : Colors.transparent,
                            borderRadius: borderRadius,
                          ),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 15),
                            child: Text(
                              item.label,
                              style: uiTextStyles.body14.copyWith(
                                color: isSelected ? uiColors.primaryColor : uiColors.backgroundSecondaryColor,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );

    overlay.insert(_overlayEntry!);
    _animationController.forward();
  }

  void remove() {
    _animationController.reverse().then((_) {
      _overlayEntry?.remove();
      _overlayEntry = null;
      _animationController.dispose();
    });
  }
}
