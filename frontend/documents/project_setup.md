# Installation

`themasteroflaw App` can run on different platforms, but you need to follow similar instructions for all of them:

1. Follow official documentation to install flutter [Flutter](https://flutter.dev/docs/get-started/install) and make sure it works (`flutter doctor -v` can help);
2. Clone the [themasteroflaw](
   //TODO add link
   ) repository (You need to have [git](https://git-scm.com) installed and also be permitted to access the repository);
3. Switch to `main` branch for the latest changes (`git switch main`);
4. Run `flutter pub get` to pull the dependencies of the application.

# Environments setup

This project contains 3 flavors:

- development
- staging
- production

(in order to be able to run staging or production, you will need to add env/env.production or env/env.staging files)

To run the desired flavor either use the launch configuration in VSCode/Android Studio or use the following commands:

```sh
# Development
$ flutter run --flavor development --target lib/main_development.dart

# Staging
$ flutter run --flavor staging --target lib/main_staging.dart

# Production
$ flutter run --flavor production --target lib/main_production.dart
```
