## Project Sctipts

The purpose of these project scripts is to simplify and speed up routine code writing processes by manipulating files with code to efficiently perform modifications or chore tasks.
Any new script idea that will optimize our workflow is highly appreciated;

Currently we have 2 major script. More to be added hopefully:

1. `Dart Export Script: This script exports all Dart files within the lib directory and creates barrel files for each subfolder. After making changes to your code, you can run:`

```bash
./exp.sh
```

`This will ensure that every file in the Flutter project is exported from /src/, enforcing unique class names and simplifying code management.`

2. `Localization Script: This script simplifies adding new localized strings to the project's localizations. Run it with:`

```bash
./loc.sh "New String||ka||ახალი ტექსტი"
```

`This will create a new, typed, and localized string fuzzzyLawLocalizations.newString that is immediately available within the app.`

To set up the scripts the scripts refer to [setup_guide](../scripts/setup_info.md)
