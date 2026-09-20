import 'package:flutter/material.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

const _aiStudioKeysUrl = 'https://aistudio.google.com/apikey';
const _cloudCredentialsUrl =
    'https://console.cloud.google.com/apis/credentials';

class ApiKeyPromptPage extends StatefulWidget {
  const ApiKeyPromptPage({super.key});

  @override
  State<ApiKeyPromptPage> createState() => _ApiKeyPromptPageState();
}

class _ApiKeyPromptPageState extends State<ApiKeyPromptPage> {
  final _controller = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _open(String url) =>
      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);

  Future<void> _submit() async {
    final key = _controller.text.trim();
    if (key.isEmpty) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final secureStorage = sl.get<SecureStorageService>();
    try {
      // Persist first so the auth interceptor attaches the key to the check
      // itself; a key that fails is deleted again below, so a typo never
      // survives this screen.
      await secureStorage.saveData('temporary_api_key', key);

      final result = await ApiKeyValidationDataSource().validate();

      if (!mounted) return;

      switch (result) {
        case ApiKeyCheck.valid:
          context.go('/cases');
        case ApiKeyCheck.invalid:
          await secureStorage.deleteData('temporary_api_key');
          if (mounted) {
            setState(
              () => _error =
                  'გასაღები არ მუშაობს. შეამოწმეთ, სრულად დააკოპირეთ '
                  'თუ არა Google AI Studio-დან.',
            );
          }
        case ApiKeyCheck.unreachable:
          // The key is NOT deleted here: the server being down says nothing
          // about it, and wiping a good key would make an outage look like
          // the user's mistake.
          if (mounted) {
            setState(
              () => _error =
                  'სერვერთან დაკავშირება ვერ მოხერხდა. '
                  'სცადეთ ხელახლა.',
            );
          }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Scaffold(
      appBar: AppBar(title: const Text('დაწყება')),
      body: SingleChildScrollView(
        padding: density.screen,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'თქვენი Google AI Studio-ს გასაღები',
              // Was `TextStyle(fontSize: 24, fontWeight: bold)` — a BLOCKING
              // literal size AND a hand-rolled weight. A brand pack owns the
              // type scale; 24/bold is `titleM`, the role every other page
              // header in this app took at M3–M9b.
              style: type.titleM.copyWith(color: colors.ink),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.m),
            Text(
              'აპლიკაცია თქვენი საკუთარი Google-ის გასაღებით მუშაობს. '
              'გასაღები უფასოა და მისი აღება ორ წუთს არ წაგართმევთ.',
              style: type.body.copyWith(color: colors.inkMute),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xl),
            FuzzzyCard(
              sectionHeader: 'როგორ მივიღოთ უფასო გასაღები',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const _GuideStep(
                    number: '1',
                    text:
                        'გადადით aistudio.google.com/apikey-ზე და შედით '
                        'თქვენი Google-ის ანგარიშით.',
                  ),
                  const _GuideStep(
                    number: '2',
                    text:
                        'დააჭირეთ ღილაკს „Create API key“. გასაღები უფასოა — '
                        'საბანკო ბარათი არ დაგჭირდებათ.',
                  ),
                  const _GuideStep(
                    number: '3',
                    text:
                        'დააკოპირეთ გასაღები (იწყება „AIza“-თი) და ჩასვით '
                        'ქვემოთ, ველში.',
                  ),
                  SizedBox(height: space.m),
                  FuzzzyButton(
                    label: 'Google AI Studio-ს გახსნა',
                    variant: FuzzzyButtonVariant.secondary,
                    icon: const Icon(Icons.open_in_new),
                    onPressed: () => _open(_aiStudioKeysUrl),
                  ),
                ],
              ),
            ),
            SizedBox(height: space.m),
            FuzzzyCard(
              sectionHeader: 'რჩევა: შეზღუდეთ გასაღები',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'სჯობს, გასაღები მხოლოდ ამ დანიშნულებით შეზღუდოთ: მაშინ, '
                    'სხვის ხელში რომც მოხვდეს, Google-ის სხვა სერვისებზე '
                    'ვერავინ დახარჯავს.',
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                  SizedBox(height: space.m),
                  const _GuideStep(
                    number: '1',
                    text:
                        'გადადით Google Cloud Console-ის „Credentials“ გვერდზე '
                        'და აირჩიეთ თქვენი გასაღები.',
                  ),
                  const _GuideStep(
                    number: '2',
                    text:
                        '„API restrictions“-ში აირჩიეთ „Restrict key“ და '
                        'მონიშნეთ მხოლოდ „Generative Language API“.',
                  ),
                  const _GuideStep(
                    number: '3',
                    text:
                        'დააჭირეთ „Save“. გასაღების წაშლა ან შეცვლა '
                        'ნებისმიერ დროს შეგეძლებათ.',
                  ),
                  SizedBox(height: space.m),
                  FuzzzyButton(
                    label: 'Google Cloud Console-ის გახსნა',
                    variant: FuzzzyButtonVariant.ghost,
                    icon: const Icon(Icons.open_in_new),
                    onPressed: () => _open(_cloudCredentialsUrl),
                  ),
                ],
              ),
            ),
            SizedBox(height: space.m),
            Text(
              'გასაღები მხოლოდ თქვენს მოწყობილობაზე ინახება. სერვერს ის '
              'მხოლოდ თქვენივე კითხვებზე პასუხის მისაღებად გადაეცემა და '
              'არსად იწერება.',
              style: type.bodyS.copyWith(color: colors.inkMute),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xl),
            TextField(
              controller: _controller,
              style: type.body.copyWith(color: colors.fieldText),
              // The local `OutlineInputBorder()` is deleted: fill, all five
              // border states, radius, content padding and hint style come
              // from M1's inputDecorationTheme (RUN_BRIEF §4). The fork's bare
              // outline was the ONE field in the app that opted out.
              decoration: const InputDecoration(hintText: 'AIza...'),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _submit(),
            ),
            if (_error != null) ...[
              SizedBox(height: space.m),
              Text(
                _error!,
                // `Colors.red` → `destructiveText`, the legible red. This is
                // the screen's only red and it is duty 4's idle text form.
                style: type.body.copyWith(color: colors.destructiveText),
                textAlign: TextAlign.center,
              ),
            ],
            SizedBox(height: space.xxl),
            SizedBox(
              width: double.infinity,
              // Dimension: the full-width CTA height. 50 → the 48 every other
              // full-width CTA in this app uses (M8's add-fact button).
              height: 48,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.actionPrimaryBg,
                  foregroundColor: colors.actionPrimaryFg,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                ),
                // Was `TextStyle(fontSize: 16)` — the second BLOCKING literal.
                // A button label is `control`, always.
                child: Text('გაგრძელება', style: type.control),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GuideStep extends StatelessWidget {
  const _GuideStep({required this.number, required this.text});

  final String number;
  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;

    return Padding(
      padding: EdgeInsets.only(bottom: space.s),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$number.',
            style: type.body.copyWith(color: colors.inkMute),
          ),
          SizedBox(width: space.s),
          Expanded(
            child: Text(text, style: type.body.copyWith(color: colors.ink)),
          ),
        ],
      ),
    );
  }
}
