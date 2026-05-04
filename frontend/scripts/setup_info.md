**Step0. Install Python 3.10 or newer if you do not have one:**
[https://www.python.org/downloads/](https://www.python.org/downloads/)

**Step1. Option 1: Run from `scripts` folder:**

```bash
chmod +x setup.sh
chmod +x runner.sh
./setup.sh
```

**Step1: Option 2: Or Alternatively Run from Flutter project root:**

```bash
chmod +x scripts/setup.sh
chmod +x scripts/runner.sh
./scripts/setup.sh
```

**Step2: Option 1: Start using scripts (from Flutter project root) by running**

```bash
./scripts/runner.sh <name_of_the_script>.py <script_parameters>
```

**Step2: Option 2: Start using scripts with predefined runners in Flutter project root**

`Enable them first:`

```bash
chmod +x exp_f.sh
chmod +x exp.sh
chmod +x loc.sh
```

`For exporting all Dart files inside lib, creating barrel files for every subfolder:`

```bash
./exp.sh
```

`For exporting all Dart files inside a custom directory:`

```bash
./exp_f.sh lib/src/custom_path
```

`For simply adding a new localized string in project localizations:`

```bash
./loc.sh "New String||ka||ახალი ტექსტი"
```
