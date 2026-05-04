import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:ui_kit/ui_kit.dart';

part '{{name.snakeCase()}}_page_state_modifier_extension.dart';

class {{name.pascalCase()}}Page extends StatelessWidget {
  const {{name.pascalCase()}}Page({super.key});

  static const routeName = '{{name.camelCase()}}Page';

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: const [
        //TODO Provide your cubits here or remove if not needed
      ],
      child: const _Provided{{name.pascalCase()}}Page(),
    );
  }
}

class _Provided{{name.pascalCase()}}Page extends StatefulWidget {
  const _Provided{{name.pascalCase()}}Page();

  @override
  State<_Provided{{name.pascalCase()}}Page> createState() => _Provided{{name.pascalCase()}}PageState();
}

class _Provided{{name.pascalCase()}}PageState extends State<_Provided{{name.pascalCase()}}Page> {
  final TextEditingController amountController = TextEditingController();

  String inputAmount = '';

  bool get isReadyToSubmit => inputAmount.isNotEmpty;

  @override
  void initState() {
    amountController.addListener(onAmountChanged);
    super.initState();
  }

  @override
  void dispose() {
    amountController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return PrimaryScaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            //TODO add title
            Text(
              '{{name.pascalCase()}} Amount',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            PrimaryTextField(
              controller: amountController,
              keyboardType: TextInputType.number,
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp('[0-9]')),
              ],
              hint: 'Enter Amount',
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: PrimaryButton(
                onPressed: onSubmit,
                //TODO add correct label
                label: 'Change Me',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
