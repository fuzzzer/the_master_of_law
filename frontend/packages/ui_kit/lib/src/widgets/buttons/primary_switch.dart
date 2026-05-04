import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimarySwitch extends StatefulWidget {
  const PrimarySwitch({super.key, required this.isSwitchOn, this.isDisabled = false, this.onChanged});

  final bool isDisabled;
  final bool isSwitchOn;
  final void Function(bool isSwitched)? onChanged;

  @override
  State<PrimarySwitch> createState() => _PrimarySwitchState();
}

class _PrimarySwitchState extends State<PrimarySwitch> {
  bool isSwitched = false;

  @override
  void initState() {
    super.initState();
    isSwitched = widget.isSwitchOn;
  }

  void _toggleSwitch() {
    if (widget.isDisabled) return;

    final newValue = !isSwitched;
    widget.onChanged?.call(newValue);
    setState(() {
      isSwitched = newValue;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;

    return GestureDetector(
      onTap: _toggleSwitch,
      child: AnimatedContainer(
        duration: Durations.medium1,
        width: 44,
        height: 24,
        padding: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          color: isSwitched
              ? (widget.isDisabled ? uiColors.secondaryColor : uiColors.primaryColor)
              : (widget.isDisabled ? uiColors.backgroundPrimaryColor : uiColors.backgroundPrimaryColor),
          borderRadius: BorderRadius.circular(20),
        ),
        child: AnimatedAlign(
          duration: Durations.medium1,
          alignment: isSwitched ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            width: 20,
            height: 20,
            decoration: BoxDecoration(
              color: widget.isDisabled ? uiColors.backgroundSecondaryColor : uiColors.primaryColor,
              shape: BoxShape.circle,
            ),
          ),
        ),
      ),
    );
  }
}
