import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

/// The dropdown can have values of type T, as the label or visual
/// representation of the dropdown might differ from its underlying value.
/// The underlying value can be specified using [PrimaryDropdown<Object>] or [DropdownItem<Object>]
class PrimaryDropdown<T> extends StatefulWidget {
  final List<DropdownItem<T>> items;
  final void Function(DropdownItem<T> item) onChanged;
  final String? selectorTitle;
  final DropdownItem<T>? selectedItem;
  final Widget? prefixWidget;
  final double? stepWidth;
  final Color? borderColor;
  final Color backgroundColor;
  final EdgeInsets? contentPadding;

  const PrimaryDropdown({
    super.key,
    required this.items,
    required this.onChanged,
    this.selectorTitle,
    this.selectedItem,
    this.prefixWidget,
    this.stepWidth,
    this.borderColor,
    this.backgroundColor = Colors.transparent,
    this.contentPadding,
  });

  @override
  State<PrimaryDropdown<T>> createState() => _PrimaryDropdownState<T>();
}

class _PrimaryDropdownState<T> extends State<PrimaryDropdown<T>> with SingleTickerProviderStateMixin {
  /// Keeps track of all dropdowns that currently have their overlay open so we
  /// can automatically hide others when one gains focus.
  static final Set<_PrimaryDropdownState> _openDropdowns = <_PrimaryDropdownState>{};

  final LayerLink _layerLink = LayerLink();
  final FocusNode _focusNode = FocusNode(debugLabel: 'PrimaryDropdown');
  OverlayEntry? _overlayEntry;
  DropdownItem? _selectedItem;

  @override
  void initState() {
    super.initState();
    _selectedItem = widget.selectedItem;
    _focusNode.addListener(_handleFocusChange);
  }

  @override
  void didUpdateWidget(covariant PrimaryDropdown<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selectedItem != oldWidget.selectedItem) {
      _selectedItem = widget.selectedItem;
    }
  }

  void _handleFocusChange() {
    if (!_focusNode.hasFocus) {
      _hideDropdown();
    }
  }

  void _toggleDropdown() {
    if (_overlayEntry != null) {
      _hideDropdown();
    } else {
      _focusNode.requestFocus();
      _showDropdown();
    }
  }

  void _showDropdown() {
    for (final dropdown in _openDropdowns.toList()) {
      if (dropdown != this) {
        dropdown._hideDropdown();
      }
    }
    _openDropdowns.add(this);

    final overlay = Overlay.of(context);
    final renderBox = context.findRenderObject() as RenderBox;
    final size = renderBox.size;

    _overlayEntry = OverlayEntry(
      builder: (context) => _buildOverlayContent(size),
    );

    overlay.insert(_overlayEntry!);
    setState(() {});
  }

  Widget _buildOverlayContent(Size size) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;
    final uiFormStyles = theme.extension<UiFormStyles>()!;

    return Positioned(
      width: size.width,
      child: CompositedTransformFollower(
        link: _layerLink,
        showWhenUnlinked: false,
        offset: Offset(0, size.height + 8),
        child: Material(
          borderRadius: BorderRadius.circular(16),
          color: uiColors.backgroundPrimaryColor,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 300),
            child: ListView.builder(
              padding: EdgeInsets.zero,
              shrinkWrap: true,
              itemCount: widget.items.length,
              itemBuilder: (context, index) {
                final item = widget.items[index];
                final isSelected = item == _selectedItem;

                return InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () => _selectItem(item),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isSelected ? uiColors.backgroundSecondaryColor : Colors.transparent,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    padding: uiFormStyles.widgetContentPadding,
                    child: Text(
                      item.label,
                      style: uiTextStyles.bodySmall12.copyWith(
                        color: isSelected ? uiColors.primaryColor : uiColors.backgroundPrimaryColor,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  void _selectItem(DropdownItem<T> item) {
    setState(() => _selectedItem = item);
    widget.onChanged(item);
    _hideDropdown();
  }

  void _hideDropdown() {
    _overlayEntry?.remove();
    _overlayEntry = null;
    _openDropdowns.remove(this);
    setState(() {});
  }

  @override
  void dispose() {
    _openDropdowns.remove(this);
    _focusNode.removeListener(_handleFocusChange);
    _focusNode.dispose();
    _hideDropdown();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;
    final uiFormStyles = theme.extension<UiFormStyles>()!;

    return FocusableActionDetector(
      focusNode: _focusNode,
      autofocus: false,
      actions: {
        ActivateIntent: CallbackAction<ActivateIntent>(
          onInvoke: (_) => _toggleDropdown(),
        ),
        DismissIntent: CallbackAction<DismissIntent>(
          onInvoke: (_) => _hideDropdown(),
        ),
      },
      child: Semantics(
        button: true,
        label: widget.selectorTitle,
        child: CompositedTransformTarget(
          link: _layerLink,
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: _toggleDropdown,
            child: Container(
              width: widget.stepWidth,
              decoration: BoxDecoration(
                border: Border.all(
                  color: widget.borderColor ?? uiColors.backgroundPrimaryColor,
                ),
                borderRadius: BorderRadius.circular(uiFormStyles.borderRadiusValue),
                color: widget.backgroundColor,
              ),
              child: Padding(
                padding: widget.contentPadding ?? uiFormStyles.scrollPadding,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    if (widget.prefixWidget != null) widget.prefixWidget!,
                    Expanded(
                      child: Text(
                        _selectedItem?.label ?? widget.selectorTitle ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: uiTextStyles.body16,
                      ),
                    ),
                    Icon(
                      _overlayEntry == null ? Icons.arrow_downward : Icons.arrow_upward,
                      color: uiColors.backgroundPrimaryColor,
                      size: 16,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
