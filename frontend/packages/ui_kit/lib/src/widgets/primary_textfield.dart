import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:ui_kit/ui_kit.dart';

class PrimaryTextField extends StatefulWidget {
  const PrimaryTextField({
    super.key,
    this.labelText,
    this.labelStyle,
    this.floatingLabelStyle,
    this.valueStyle,
    this.errorStyle,
    this.backgroundColor,
    this.borderColor,
    this.focusColor,
    this.errorColor,
    this.controller,
    this.forcedErrorText,
    this.hasForcedError = false,
    this.keyboardType = TextInputType.text,
    this.maxLines = 1,
    this.borderRadiusValue = 48,
    this.width,
    this.contentPadding,
    this.scrollPadding,
    this.isDisabled = false,
    this.obscureText = false,
    this.showObscureToggle = false,
    this.prefixWidget,
    this.suffixWidget,
    this.onChanged,
    this.validator,
    this.focusNode,
    this.inputFormatters,
    this.maxLength,
    this.onUnfocused,
    this.startsValidationWithoutUnfocus = false,
    this.hint,
    this.cursorColor,
    this.additionalInlineInfo,
    this.autocorrect = false,
    this.enableSuggestions = false,
  });

  final String? labelText;
  final TextStyle? labelStyle;
  final TextStyle? floatingLabelStyle;
  final TextStyle? valueStyle;
  final TextStyle? errorStyle;
  final Color? backgroundColor;
  final Color? borderColor;
  final Color? focusColor;
  final Color? errorColor;
  final TextEditingController? controller;
  final String? forcedErrorText;

  ///true [hasForcedError] parameter overrides the validator error text value with forced Error text
  final bool hasForcedError;
  final TextInputType keyboardType;
  final int maxLines;
  final double borderRadiusValue;
  final double? width;
  final EdgeInsets? contentPadding;
  final EdgeInsets? scrollPadding;
  final bool isDisabled;
  final bool obscureText;
  final bool showObscureToggle;
  final Widget? prefixWidget;
  final Widget? suffixWidget;
  final void Function(String value)? onChanged;
  final String? Function(String currentText)? validator;
  final FocusNode? focusNode;
  final List<TextInputFormatter>? inputFormatters;
  final int? maxLength;
  final VoidCallback? onUnfocused;
  final bool startsValidationWithoutUnfocus;
  final String? hint;
  final Color? cursorColor;
  final String? additionalInlineInfo;
  final bool autocorrect;
  final bool enableSuggestions;

  @override
  State<PrimaryTextField> createState() => _PrimaryTextFieldState();
}

class _PrimaryTextFieldState extends State<PrimaryTextField> with SingleTickerProviderStateMixin {
  final formFieldKey = GlobalKey<FormFieldState>();

  late final FocusNode _focusNode;
  late final TextEditingController _controller;

  late bool isTextObscured;
  bool hasFocus = false;

  bool validatesContentOnChanged = false;

  double inputWidth = 0;

  String currentTextValue = '';

  @override
  void initState() {
    super.initState();

    _focusNode = widget.focusNode ?? FocusNode();
    _controller = widget.controller ?? TextEditingController();

    currentTextValue = _controller.text;

    isTextObscured = widget.obscureText;

    _focusNode.addListener(() {
      final isUnfocused = hasFocus && !_focusNode.hasFocus;

      if (isUnfocused) onUnfocused();

      setState(() {
        hasFocus = _focusNode.hasFocus;
      });
    });

    if (widget.startsValidationWithoutUnfocus) {
      startValidatingContentOnChanged();
    }
  }

  @override
  void dispose() {
    _focusNode.removeListener(() {});

    if (widget.focusNode == null) {
      _focusNode.dispose();
    }

    if (widget.controller == null) {
      _controller.dispose();
    }

    super.dispose();
  }

  void onUnfocused() {
    validateContent();

    startValidatingContentOnChanged();

    if (widget.onUnfocused != null) widget.onUnfocused!();
  }

  void startValidatingContentOnChanged() {
    setState(() {
      validatesContentOnChanged = true;
    });
  }

  void validateContent() {
    formFieldKey.currentState?.validate();
  }

  void toggleObscureText() {
    setState(() {
      isTextObscured = !isTextObscured;
    });
  }

  void setInputWidth() {
    setState(() {
      inputWidth = calculateTextWidth(
        text: _controller.text,
        style: widget.valueStyle ?? UiKitTextStyles.body16,
      );
    });
  }

  double calculateTextWidth({
    required String text,
    required TextStyle style,
  }) {
    final TextPainter textPainter = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    )..layout();

    return textPainter.size.width;
  }

  void onChanged(String value) {
    setState(() {
      currentTextValue = value;
    });

    if (widget.additionalInlineInfo != null) {
      setInputWidth();
    }

    if (widget.onChanged != null) {
      widget.onChanged!(value);
    }

    if (validatesContentOnChanged) {
      validateContent();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uiColors = theme.extension<UiColors>()!;
    final uiTextStyles = theme.extension<UiTextStyles>()!;
    final uiFormStyles = theme.extension<UiFormStyles>()!;

    final borderColor =
        widget.borderColor ?? (widget.isDisabled ? Colors.transparent : uiColors.backgroundSecondaryColor);
    final backgroundColor =
        widget.backgroundColor ?? (widget.isDisabled ? uiColors.backgroundPrimaryColor : Colors.transparent);
    final focusColor = widget.focusColor ?? uiColors.backgroundPrimaryColor;
    final errorColor = widget.errorColor ?? uiColors.errorColor;

    final labelStyle = widget.labelStyle ?? uiTextStyles.body16.copyWith(color: uiColors.backgroundSecondaryColor);
    final floatingLabelStyle =
        widget.floatingLabelStyle ?? uiTextStyles.body14.copyWith(color: uiColors.backgroundSecondaryColor);
    final valueStyle = widget.valueStyle ?? uiTextStyles.body16.copyWith(color: uiColors.primaryColor);
    final errorStyle = widget.errorStyle ?? uiTextStyles.body14.copyWith(color: uiColors.errorColor);

    final width = widget.width ?? double.maxFinite;
    final hasPrefixWidget = widget.prefixWidget != null;
    final hasSuffixWidget = widget.suffixWidget != null;

    final contentPadding = widget.contentPadding ?? uiFormStyles.widgetContentPadding;

    return FormField<String>(
      key: formFieldKey,
      validator: widget.validator != null ? (_) => widget.validator!(_controller.text) : null,
      builder: (fieldState) {
        final hasValidatorError = fieldState.hasError;
        final validatorErrorText = fieldState.errorText;

        final hasError = widget.hasForcedError || hasValidatorError;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: width,
              decoration: BoxDecoration(
                border: Border.all(
                  color: hasError
                      ? errorColor
                      : hasFocus
                      ? focusColor
                      : borderColor,
                ),
                borderRadius: BorderRadius.circular(widget.borderRadiusValue),
                color: backgroundColor,
              ),
              child: Padding(
                padding: contentPadding,
                child: Row(
                  spacing: uiFormStyles.rowSpacing,
                  children: [
                    if (hasPrefixWidget) widget.prefixWidget!,
                    Expanded(
                      child: Stack(
                        children: [
                          TextField(
                            autocorrect: widget.autocorrect,
                            enableSuggestions: widget.enableSuggestions,
                            inputFormatters: [
                              if (widget.inputFormatters != null) ...widget.inputFormatters!,
                              LengthLimitingTextInputFormatter(widget.maxLength),
                            ],
                            style: valueStyle,
                            cursorColor: widget.cursorColor,
                            focusNode: _focusNode,
                            controller: _controller,
                            keyboardType: widget.keyboardType,
                            obscureText: widget.obscureText ? isTextObscured : false,
                            onChanged: onChanged,
                            scrollPadding: widget.scrollPadding ?? uiFormStyles.scrollPadding,
                            maxLines: widget.maxLines,
                            enabled: !widget.isDisabled,
                            decoration: InputDecoration(
                              labelText: widget.labelText,
                              labelStyle: labelStyle,
                              floatingLabelStyle: floatingLabelStyle,
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.zero,
                              isDense: true,
                              hint: widget.hint != null
                                  ? Text(
                                      widget.hint!,
                                      style: uiTextStyles.body16.copyWith(
                                        color: uiColors.backgroundSecondaryColor,
                                      ),
                                    )
                                  : null,
                            ),
                          ),
                          if (widget.additionalInlineInfo != null && currentTextValue.isNotEmpty)
                            Builder(
                              builder: (context) {
                                return Positioned(
                                  left: inputWidth,
                                  child: IgnorePointer(
                                    child: Text(
                                      '  ${widget.additionalInlineInfo}',
                                      style: widget.valueStyle ?? valueStyle,
                                    ),
                                  ),
                                );
                              },
                            ),
                        ],
                      ),
                    ),
                    if (widget.showObscureToggle)
                      GestureDetector(
                        onTap: toggleObscureText,
                        child: Icon(
                          isTextObscured ? Icons.visibility : Icons.visibility_off,
                          color: uiColors.backgroundSecondaryColor,
                          size: 16,
                        ),
                      ),
                    if (widget.showObscureToggle && hasSuffixWidget)
                      Container(
                        height: 16,
                        width: 1,
                        color: uiColors.secondaryColor,
                      ),
                    if (hasSuffixWidget) widget.suffixWidget!,
                  ],
                ),
              ),
            ),
            if (hasError && validatorErrorText?.isNotEmpty == true || widget.forcedErrorText?.isNotEmpty == true)
              const SizedBox(height: 6),
            if (widget.hasForcedError && widget.forcedErrorText?.isNotEmpty == true)
              Text(
                widget.forcedErrorText!,
                style: errorStyle,
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            if (hasValidatorError && validatorErrorText?.isNotEmpty == true)
              Text(
                validatorErrorText!,
                style: errorStyle,
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
          ],
        );
      },
    );
  }
}
