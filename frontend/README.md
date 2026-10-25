## Project Description

- [Project Description](documents/description.md) - Here you'll find an in-depth overview of fuzzzy_law's description of features, architecture and etc..

- [How to Work With Various Modules](documents/modules.md) - Here you'll find some guides of how to work with various modules, like translations in the app, etc..

## Getting Started

- [Project Setup](documents/project_setup.md) - Instructions on how to clone the repository, install dependencies, and run the application on various platforms (Android, iOS).

## App flow checks

Five reader journeys (first launch on the key screen, saving a Google key, a new case,
a chat answer, the laws browser) run against an in-memory fake backend, so no key or
server is needed. The flows live in `test/app_flows/app_flows.dart`.

- `scripts/run_app_flows.sh` runs them as widget tests (no device).
- `scripts/run_app_flows.sh -d <device-id>` also runs `integration_test/app_flows_test.dart`
  on a device or emulator; `-d chrome` or `-d web-server` uses `flutter drive` and needs
  `chromedriver` on the PATH.

A check skipped for a known defect names it in a constant at the bottom of
`app_flows.dart`; clear the constant when the defect is fixed.

## Contributing

- [Contribution](documents/contribution.md) - Guidelines for contributing to fuzzzy_law, covering code style, pull request process, bug reporting, and feature requests.

- [Code Generation](documents/code_generation.md) - Information about any automated code generation processes used in the project to generate templates for various kind of services, following project structure and coding style.

- [Project Scripts](documents/project_scripts.md) - A list of scripts to simplify development, like simply adding new localizations, code management simplification and etc.

## End-User Documentation

- [User Guide](documents/user_guide.md) - Instructions for end-users on how to use fuzzzy_law, including account creation, navigation, and gameplay features.
