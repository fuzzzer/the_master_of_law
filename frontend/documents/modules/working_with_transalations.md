## Working with Translations 🌐

### Adding Strings

1. To add a new localizable string, open the `app_en.arb` file at `lib/core/l10n/arb/app_en.arb`.

```arb
{
    "@@locale": "en",
    "continue": "Continue",
    "@continue": {
        "description": "default continue text prompting user to continue some process"
    }
}
```

After adding new sting in the default template arb file, you can add translations in other localization files like `app_ka.arb and generate dart bindings

### Generating Translations

To use the latest translations arb file changes, you will need to generate them.
Generate localizations for the current project with:

```sh
flutter gen-l10n
```

Or simply [setup](../../scripts/setup_info.md) ./loc.sh script and use it from project root like this:

```bash
./loc.sh "New String||ka||ახალი ტექსტი"
```

### Using Localizations

```dart
import 'package:themasteroflaw/src/src_exports.dart';

@override
Widget build(BuildContext context) {
  final localizations = context.themasteroflawLocalizations;
  return Text(localizations.helloWorld);
}
```

[flutter_localizations_link]: https://api.flutter.dev/flutter/flutter_localizations/flutter_localizations-library.html
[internationalization_link]: https://flutter.dev/docs/development/accessibility-and-localization/internationalization

### Using Localizat
