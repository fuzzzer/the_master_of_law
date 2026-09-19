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
                  'გასაღები არ მუშაობს. დარწმუნდით, რომ სრულად '
                  'დააკოპირეთ Google AI Studio-დან.',
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
                  'გთხოვთ, სცადოთ თავიდან.',
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
              'შეიყვანეთ Google AI Studio-ს გასაღები',
              // Was `TextStyle(fontSize: 24, fontWeight: bold)` — a BLOCKING
              // literal size AND a hand-rolled weight. A brand pack owns the
              // type scale; 24/bold is `titleM`, the role every other page
              // header in this app took at M3–M9b.
              style: type.titleM.copyWith(color: colors.ink),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.m),
            Text(
              'აპლიკაცია იყენებს თქვენს პირად Google-ის გასაღებს — ის უფასოა '
              'და აღება ორ წუთს არ სჭირდება.',
              style: type.body.copyWith(color: colors.inkMute),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xl),
            FuzzzyCard(
              sectionHeader: 'როგორ ავიღოთ უფასო გასაღები',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const _GuideStep(
                    number: '1',
                    text:
                        'გახსენით aistudio.google.com/apikey და შედით '
                        'თქვენი Google-ის ანგარიშით.',
                  ),
                  const _GuideStep(
                    number: '2',
                    text:
                        'დააჭირეთ „Create API key“. გასაღები უფასოა — '
                        'საბანკო ბარათი არ არის საჭირო.',
                  ),
                  const _GuideStep(
                    number: '3',
                    text:
                        'დააკოპირეთ გასაღები (იწყება „AIza“-თი) და ჩასვით '
                        'ქვემოთ ველში.',
                  ),
                  SizedBox(height: space.m),
                  FuzzzyButton(
                    label: 'გახსენით Google AI Studio',
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
                    'შეზღუდული გასაღები მხოლოდ AI-ს პასუხებზე მუშაობს — '
                    'გაჟონვის შემთხვევაშიც სხვა Google-ის სერვისებზე ვერავინ '
                    'გამოიყენებს.',
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                  SizedBox(height: space.m),
                  const _GuideStep(
                    number: '1',
                    text:
                        'გახსენით Google Cloud Console → Credentials და '
                        'აირჩიეთ თქვენი გასაღები.',
                  ),
                  const _GuideStep(
                    number: '2',
                    text:
                        '„API restrictions“ → „Restrict key“ → მონიშნეთ '
                        'მხოლოდ „Generative Language API“.',
                  ),
                  const _GuideStep(
                    number: '3',
                    text:
                        'დააჭირეთ „Save“. გასაღების წაშლა ან შეცვლა '
                        'ნებისმიერ დროს შეგიძლიათ.',
                  ),
                  SizedBox(height: space.m),
                  FuzzzyButton(
                    label: 'გახსენით Google Cloud Console',
                    variant: FuzzzyButtonVariant.ghost,
                    icon: const Icon(Icons.open_in_new),
                    onPressed: () => _open(_cloudCredentialsUrl),
                  ),
                ],
              ),
            ),
            SizedBox(height: space.m),
            Text(
              'გასაღები ინახება მხოლოდ ამ მოწყობილობაზე და იგზავნება მხოლოდ '
              'თქვენს კითხვებზე პასუხის მისაღებად — სერვერზე არ ინახება.',
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
            style: type.data.copyWith(color: colors.ink),
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
