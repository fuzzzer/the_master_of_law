// ignore_for_file: invalid_use_of_protected_member

part of '{{name.snakeCase()}}_page.dart';

extension _Provided{{name.pascalCase()}}PageModifierExtension on _Provided{{name.pascalCase()}}PageState {
  void onAmountChanged() {
    setState(() {
      inputAmount = amountController.text;
    });
    //TODO Optionally add more logic
  }

  void onSubmit() {
    //TODO Add your submit logic
  }
}