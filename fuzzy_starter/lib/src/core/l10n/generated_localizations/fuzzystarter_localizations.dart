import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'fuzzystarter_localizations_en.dart';
import 'fuzzystarter_localizations_ka.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of FuzzystarterLocalizations
/// returned by `FuzzystarterLocalizations.of(context)`.
///
/// Applications need to include `FuzzystarterLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated_localizations/fuzzystarter_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: FuzzystarterLocalizations.localizationsDelegates,
///   supportedLocales: FuzzystarterLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the FuzzystarterLocalizations.supportedLocales
/// property.
abstract class FuzzystarterLocalizations {
  FuzzystarterLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static FuzzystarterLocalizations? of(BuildContext context) {
    return Localizations.of<FuzzystarterLocalizations>(
      context,
      FuzzystarterLocalizations,
    );
  }

  static const LocalizationsDelegate<FuzzystarterLocalizations> delegate =
      _FuzzystarterLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ka'),
  ];

  /// No description provided for @languageName.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get languageName;

  /// No description provided for @smsCode.
  ///
  /// In en, this message translates to:
  /// **'SMS Code'**
  String get smsCode;

  /// No description provided for @getCode.
  ///
  /// In en, this message translates to:
  /// **'Get Code'**
  String get getCode;

  /// No description provided for @authorization.
  ///
  /// In en, this message translates to:
  /// **'Authorization'**
  String get authorization;

  /// No description provided for @registration.
  ///
  /// In en, this message translates to:
  /// **'Registration'**
  String get registration;

  /// No description provided for @userName.
  ///
  /// In en, this message translates to:
  /// **'User Name'**
  String get userName;

  /// No description provided for @user.
  ///
  /// In en, this message translates to:
  /// **'User'**
  String get user;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @login.
  ///
  /// In en, this message translates to:
  /// **'Login'**
  String get login;

  /// No description provided for @loginWithSms.
  ///
  /// In en, this message translates to:
  /// **'Login with SMS'**
  String get loginWithSms;

  /// No description provided for @loginWithPassword.
  ///
  /// In en, this message translates to:
  /// **'Login with Password'**
  String get loginWithPassword;

  /// No description provided for @noInternetConnectionTitle.
  ///
  /// In en, this message translates to:
  /// **'No internet connection'**
  String get noInternetConnectionTitle;

  /// No description provided for @noInternetConnectionSubTitle.
  ///
  /// In en, this message translates to:
  /// **'Check your internet connection and try again'**
  String get noInternetConnectionSubTitle;

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try Again'**
  String get tryAgain;

  /// No description provided for @sport.
  ///
  /// In en, this message translates to:
  /// **'Sport'**
  String get sport;

  /// No description provided for @live.
  ///
  /// In en, this message translates to:
  /// **'LIVE'**
  String get live;

  /// No description provided for @slots.
  ///
  /// In en, this message translates to:
  /// **'Slots'**
  String get slots;

  /// No description provided for @casino.
  ///
  /// In en, this message translates to:
  /// **'Casino'**
  String get casino;

  /// No description provided for @games.
  ///
  /// In en, this message translates to:
  /// **'Games'**
  String get games;

  /// No description provided for @p2p.
  ///
  /// In en, this message translates to:
  /// **'P2P'**
  String get p2p;

  /// No description provided for @poker.
  ///
  /// In en, this message translates to:
  /// **'Poker'**
  String get poker;

  /// No description provided for @freeSport.
  ///
  /// In en, this message translates to:
  /// **'Free Sport'**
  String get freeSport;

  /// No description provided for @campaigns.
  ///
  /// In en, this message translates to:
  /// **'Campaigns'**
  String get campaigns;

  /// No description provided for @help.
  ///
  /// In en, this message translates to:
  /// **'Help'**
  String get help;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @onlineChat.
  ///
  /// In en, this message translates to:
  /// **'Online Chat'**
  String get onlineChat;

  /// No description provided for @onlineCall.
  ///
  /// In en, this message translates to:
  /// **'Online Call'**
  String get onlineCall;

  /// No description provided for @contactInfo.
  ///
  /// In en, this message translates to:
  /// **'Contact Info'**
  String get contactInfo;

  /// No description provided for @faq.
  ///
  /// In en, this message translates to:
  /// **'FAQ'**
  String get faq;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @lariSymbol.
  ///
  /// In en, this message translates to:
  /// **'₾'**
  String get lariSymbol;

  /// No description provided for @buyBonus.
  ///
  /// In en, this message translates to:
  /// **'BUY BONUS'**
  String get buyBonus;

  /// No description provided for @invalidUsernameOrPassword.
  ///
  /// In en, this message translates to:
  /// **'Invalid username or password'**
  String get invalidUsernameOrPassword;

  /// No description provided for @wrongVeryficationCode.
  ///
  /// In en, this message translates to:
  /// **'Wrong veryfication code'**
  String get wrongVeryficationCode;

  /// No description provided for @captchaRequired.
  ///
  /// In en, this message translates to:
  /// **'Captcha required'**
  String get captchaRequired;

  /// No description provided for @wrongCaptcha.
  ///
  /// In en, this message translates to:
  /// **'Wrong captcha'**
  String get wrongCaptcha;

  /// No description provided for @wrongSmsCode.
  ///
  /// In en, this message translates to:
  /// **'Wrong SMS code'**
  String get wrongSmsCode;

  /// No description provided for @rateLimit.
  ///
  /// In en, this message translates to:
  /// **'Rate limit'**
  String get rateLimit;

  /// No description provided for @retryAfter.
  ///
  /// In en, this message translates to:
  /// **'Retry After'**
  String get retryAfter;

  /// No description provided for @wrongDeviceCode.
  ///
  /// In en, this message translates to:
  /// **'Wrong device code'**
  String get wrongDeviceCode;

  /// No description provided for @customerNotFoundWithSpecifiedPhoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Customer not found with specified phone number'**
  String get customerNotFoundWithSpecifiedPhoneNumber;

  /// No description provided for @unexpectedError.
  ///
  /// In en, this message translates to:
  /// **'Unexpected Error'**
  String get unexpectedError;

  /// No description provided for @rateLimitReached.
  ///
  /// In en, this message translates to:
  /// **'Rate Limit Reached'**
  String get rateLimitReached;

  /// No description provided for @name.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get name;

  /// No description provided for @newText.
  ///
  /// In en, this message translates to:
  /// **'NEW'**
  String get newText;

  /// No description provided for @surname.
  ///
  /// In en, this message translates to:
  /// **'Surname'**
  String get surname;

  /// No description provided for @country.
  ///
  /// In en, this message translates to:
  /// **'Country'**
  String get country;

  /// No description provided for @nationality.
  ///
  /// In en, this message translates to:
  /// **'Nationality'**
  String get nationality;

  /// No description provided for @city.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get city;

  /// No description provided for @phoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Phone Number'**
  String get phoneNumber;

  /// No description provided for @personalNumber.
  ///
  /// In en, this message translates to:
  /// **'Personal Number'**
  String get personalNumber;

  /// No description provided for @day.
  ///
  /// In en, this message translates to:
  /// **'Day'**
  String get day;

  /// No description provided for @month.
  ///
  /// In en, this message translates to:
  /// **'Month'**
  String get month;

  /// No description provided for @year.
  ///
  /// In en, this message translates to:
  /// **'Year'**
  String get year;

  /// No description provided for @iHavePromoCode.
  ///
  /// In en, this message translates to:
  /// **'I have promo code'**
  String get iHavePromoCode;

  /// No description provided for @personalInformation.
  ///
  /// In en, this message translates to:
  /// **'Personal Information'**
  String get personalInformation;

  /// No description provided for @accountDetails.
  ///
  /// In en, this message translates to:
  /// **'Account Details'**
  String get accountDetails;

  /// No description provided for @repeat.
  ///
  /// In en, this message translates to:
  /// **'Repeat'**
  String get repeat;

  /// No description provided for @sufficientAgeAgreementText.
  ///
  /// In en, this message translates to:
  /// **'Sufficient Age Agreement Text'**
  String get sufficientAgeAgreementText;

  /// No description provided for @privacyPolicyAgreementText.
  ///
  /// In en, this message translates to:
  /// **'Privacy Policy Agreement Text'**
  String get privacyPolicyAgreementText;

  /// No description provided for @promoCode.
  ///
  /// In en, this message translates to:
  /// **'Promo Code'**
  String get promoCode;

  /// No description provided for @registrationIsSuccessful.
  ///
  /// In en, this message translates to:
  /// **'Registration is successful'**
  String get registrationIsSuccessful;

  /// No description provided for @registrationIsUnsuccessful.
  ///
  /// In en, this message translates to:
  /// **'Registration is unsuccessful'**
  String get registrationIsUnsuccessful;

  /// No description provided for @passwordWasSuccessfullyChangedNowYouCanLogin.
  ///
  /// In en, this message translates to:
  /// **'Password was successfully changed, now you can login'**
  String get passwordWasSuccessfullyChangedNowYouCanLogin;

  /// No description provided for @coundNotChangePassword.
  ///
  /// In en, this message translates to:
  /// **'Cound not change password'**
  String get coundNotChangePassword;

  /// No description provided for @verifyAccount.
  ///
  /// In en, this message translates to:
  /// **'Verify Account'**
  String get verifyAccount;

  /// No description provided for @continueWithoutVerification.
  ///
  /// In en, this message translates to:
  /// **'Continue Without Verification'**
  String get continueWithoutVerification;

  /// No description provided for @passwordRecovery.
  ///
  /// In en, this message translates to:
  /// **'Password Recovery'**
  String get passwordRecovery;

  /// No description provided for @bigAndSmallCharacters.
  ///
  /// In en, this message translates to:
  /// **'BIG and small characters'**
  String get bigAndSmallCharacters;

  /// No description provided for @numberForExampleOr.
  ///
  /// In en, this message translates to:
  /// **'Number (for example 1 or 123)'**
  String get numberForExampleOr;

  /// No description provided for @symbol.
  ///
  /// In en, this message translates to:
  /// **'symbol'**
  String get symbol;

  /// No description provided for @repeatPassword.
  ///
  /// In en, this message translates to:
  /// **'Repeat Password'**
  String get repeatPassword;

  /// No description provided for @enterSmsCode.
  ///
  /// In en, this message translates to:
  /// **'Enter SMS code'**
  String get enterSmsCode;

  /// No description provided for @enterNewPassword.
  ///
  /// In en, this message translates to:
  /// **'Enter New Password'**
  String get enterNewPassword;

  /// No description provided for @recoverPassword.
  ///
  /// In en, this message translates to:
  /// **'Recover Password'**
  String get recoverPassword;

  /// No description provided for @hello.
  ///
  /// In en, this message translates to:
  /// **'Hello'**
  String get hello;

  /// No description provided for @change.
  ///
  /// In en, this message translates to:
  /// **'Change'**
  String get change;

  /// No description provided for @enterYourPasscode.
  ///
  /// In en, this message translates to:
  /// **'Enter Your Passcode'**
  String get enterYourPasscode;

  /// No description provided for @forgotPasscode.
  ///
  /// In en, this message translates to:
  /// **'Forgot Passcode?'**
  String get forgotPasscode;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @forSecurityPurposesYouMustEnterTheSymbolsShownInTheImageIntoTheProvidedField.
  ///
  /// In en, this message translates to:
  /// **'For security purposes, you must enter the symbols shown in the image into the provided field.'**
  String
  get forSecurityPurposesYouMustEnterTheSymbolsShownInTheImageIntoTheProvidedField;

  /// No description provided for @theSymbolsYouEnteredAreIncorrectPleaseTryAgain.
  ///
  /// In en, this message translates to:
  /// **'The symbols you entered are incorrect, please try again'**
  String get theSymbolsYouEnteredAreIncorrectPleaseTryAgain;

  /// No description provided for @passwordsDoNotMatch.
  ///
  /// In en, this message translates to:
  /// **'Passwords do not match'**
  String get passwordsDoNotMatch;

  /// No description provided for @minimumCharacters.
  ///
  /// In en, this message translates to:
  /// **'Minimum {number} characters'**
  String minimumCharacters(Object number);

  /// No description provided for @wrongFormat.
  ///
  /// In en, this message translates to:
  /// **'Wrong format'**
  String get wrongFormat;

  /// No description provided for @useOnlyLatinLetters.
  ///
  /// In en, this message translates to:
  /// **'Use only Latin letters'**
  String get useOnlyLatinLetters;

  /// No description provided for @passwordMustNotMatchTheUsername.
  ///
  /// In en, this message translates to:
  /// **'Password must not match the username.'**
  String get passwordMustNotMatchTheUsername;

  /// No description provided for @personalNumberCantBeFound.
  ///
  /// In en, this message translates to:
  /// **'Personal Number Can\'t Be Found'**
  String get personalNumberCantBeFound;

  /// No description provided for @thePersonCouldNotBeIdentifiedPleaseCheckThePersonalInformation.
  ///
  /// In en, this message translates to:
  /// **'The person could not be identified, please check the personal information.'**
  String get thePersonCouldNotBeIdentifiedPleaseCheckThePersonalInformation;

  /// No description provided for @hasAlreadyBeenUsed.
  ///
  /// In en, this message translates to:
  /// **'Has already been used'**
  String get hasAlreadyBeenUsed;

  /// No description provided for @pleaseEnterAValidIdNumber.
  ///
  /// In en, this message translates to:
  /// **'Please enter a valid ID number'**
  String get pleaseEnterAValidIdNumber;

  /// No description provided for @faCode.
  ///
  /// In en, this message translates to:
  /// **'2FA Code'**
  String get faCode;

  /// No description provided for @january.
  ///
  /// In en, this message translates to:
  /// **'January'**
  String get january;

  /// No description provided for @february.
  ///
  /// In en, this message translates to:
  /// **'February'**
  String get february;

  /// No description provided for @march.
  ///
  /// In en, this message translates to:
  /// **'March'**
  String get march;

  /// No description provided for @april.
  ///
  /// In en, this message translates to:
  /// **'April'**
  String get april;

  /// No description provided for @may.
  ///
  /// In en, this message translates to:
  /// **'May'**
  String get may;

  /// No description provided for @june.
  ///
  /// In en, this message translates to:
  /// **'June'**
  String get june;

  /// No description provided for @july.
  ///
  /// In en, this message translates to:
  /// **'July'**
  String get july;

  /// No description provided for @august.
  ///
  /// In en, this message translates to:
  /// **'August'**
  String get august;

  /// No description provided for @september.
  ///
  /// In en, this message translates to:
  /// **'September'**
  String get september;

  /// No description provided for @october.
  ///
  /// In en, this message translates to:
  /// **'October'**
  String get october;

  /// No description provided for @november.
  ///
  /// In en, this message translates to:
  /// **'November'**
  String get november;

  /// No description provided for @december.
  ///
  /// In en, this message translates to:
  /// **'December'**
  String get december;

  /// No description provided for @couldNotReloadCaptcha.
  ///
  /// In en, this message translates to:
  /// **'Could not reload captcha'**
  String get couldNotReloadCaptcha;

  /// No description provided for @couldNotLoadCountries.
  ///
  /// In en, this message translates to:
  /// **'Could not load countries'**
  String get couldNotLoadCountries;

  /// No description provided for @georgia.
  ///
  /// In en, this message translates to:
  /// **'Georgia'**
  String get georgia;

  /// No description provided for @enterSymbols.
  ///
  /// In en, this message translates to:
  /// **'Enter Symbols'**
  String get enterSymbols;

  /// No description provided for @time.
  ///
  /// In en, this message translates to:
  /// **'Time'**
  String get time;

  /// No description provided for @buyIn.
  ///
  /// In en, this message translates to:
  /// **'Buy-In'**
  String get buyIn;

  /// No description provided for @prize.
  ///
  /// In en, this message translates to:
  /// **'Prize'**
  String get prize;

  /// No description provided for @tournaments.
  ///
  /// In en, this message translates to:
  /// **'Tournaments'**
  String get tournaments;

  /// No description provided for @noTournamentsMessage.
  ///
  /// In en, this message translates to:
  /// **'Scheduled tournaments are temporarily unavailable'**
  String get noTournamentsMessage;

  /// No description provided for @domino.
  ///
  /// In en, this message translates to:
  /// **'Domino'**
  String get domino;

  /// No description provided for @bura.
  ///
  /// In en, this message translates to:
  /// **'Bura'**
  String get bura;

  /// No description provided for @backgammon.
  ///
  /// In en, this message translates to:
  /// **'Backgammon'**
  String get backgammon;

  /// No description provided for @today.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get today;

  /// No description provided for @iConsentToTheProcessingOfMyPersonalDataForDirectMarketingPurposesConsentCanBeWithdrawnAtAnyTimeNoSms.
  ///
  /// In en, this message translates to:
  /// **'I consent to the processing of my personal data for direct marketing purposes (Consent can be withdrawn at any time. No SMS:94403).'**
  String
  get iConsentToTheProcessingOfMyPersonalDataForDirectMarketingPurposesConsentCanBeWithdrawnAtAnyTimeNoSms;

  /// No description provided for @transactionsHistory.
  ///
  /// In en, this message translates to:
  /// **'Transactions history'**
  String get transactionsHistory;

  /// No description provided for @all.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get all;

  /// No description provided for @lastWeek.
  ///
  /// In en, this message translates to:
  /// **'Last week'**
  String get lastWeek;

  /// No description provided for @lastMonth.
  ///
  /// In en, this message translates to:
  /// **'Last month'**
  String get lastMonth;

  /// No description provided for @historyIsEmpty.
  ///
  /// In en, this message translates to:
  /// **'History is empty'**
  String get historyIsEmpty;

  /// No description provided for @youCanSelectADifferentTimePeriod.
  ///
  /// In en, this message translates to:
  /// **'You can select a different time period.'**
  String get youCanSelectADifferentTimePeriod;

  /// No description provided for @clearFilters.
  ///
  /// In en, this message translates to:
  /// **'Clear filters'**
  String get clearFilters;

  /// No description provided for @deposit.
  ///
  /// In en, this message translates to:
  /// **'Deposit'**
  String get deposit;

  /// No description provided for @filter.
  ///
  /// In en, this message translates to:
  /// **'Filter'**
  String get filter;

  /// No description provided for @specificDates.
  ///
  /// In en, this message translates to:
  /// **'Specific dates'**
  String get specificDates;

  /// No description provided for @smsCodeRequestFailed.
  ///
  /// In en, this message translates to:
  /// **'Sms code request failed'**
  String get smsCodeRequestFailed;

  /// No description provided for @tomorrow.
  ///
  /// In en, this message translates to:
  /// **'Tomorrow'**
  String get tomorrow;

  /// No description provided for @spinGo.
  ///
  /// In en, this message translates to:
  /// **'SPIN & GO'**
  String get spinGo;

  /// No description provided for @spinGames.
  ///
  /// In en, this message translates to:
  /// **'Spin Games'**
  String get spinGames;

  /// No description provided for @player.
  ///
  /// In en, this message translates to:
  /// **'Player'**
  String get player;

  /// No description provided for @freeroll.
  ///
  /// In en, this message translates to:
  /// **'FreeRoll'**
  String get freeroll;

  /// No description provided for @freespin.
  ///
  /// In en, this message translates to:
  /// **'FreeSpin'**
  String get freespin;

  /// No description provided for @learnMore.
  ///
  /// In en, this message translates to:
  /// **'Learn More'**
  String get learnMore;

  /// No description provided for @minLetters.
  ///
  /// In en, this message translates to:
  /// **'Minimum 6 characters'**
  String get minLetters;

  /// No description provided for @liveRouletteJackpot.
  ///
  /// In en, this message translates to:
  /// **'LIVE ROULETTE JACKPOT'**
  String get liveRouletteJackpot;

  /// No description provided for @youDontHaveFavorites.
  ///
  /// In en, this message translates to:
  /// **'You don\'t have favorites'**
  String get youDontHaveFavorites;

  /// No description provided for @sundayShortened.
  ///
  /// In en, this message translates to:
  /// **'SUN'**
  String get sundayShortened;

  /// No description provided for @mondayShortened.
  ///
  /// In en, this message translates to:
  /// **'MON'**
  String get mondayShortened;

  /// No description provided for @tuesdayShortened.
  ///
  /// In en, this message translates to:
  /// **'TUE'**
  String get tuesdayShortened;

  /// No description provided for @wednesdayShortened.
  ///
  /// In en, this message translates to:
  /// **'WED'**
  String get wednesdayShortened;

  /// No description provided for @thursdayShortened.
  ///
  /// In en, this message translates to:
  /// **'THU'**
  String get thursdayShortened;

  /// No description provided for @fridayShortened.
  ///
  /// In en, this message translates to:
  /// **'FRI'**
  String get fridayShortened;

  /// No description provided for @saturdayShortened.
  ///
  /// In en, this message translates to:
  /// **'SAT'**
  String get saturdayShortened;

  /// No description provided for @type.
  ///
  /// In en, this message translates to:
  /// **'Type'**
  String get type;

  /// No description provided for @amount.
  ///
  /// In en, this message translates to:
  /// **'Amount'**
  String get amount;

  /// No description provided for @status.
  ///
  /// In en, this message translates to:
  /// **'Status'**
  String get status;

  /// No description provided for @withdrawal.
  ///
  /// In en, this message translates to:
  /// **'Withdrawal'**
  String get withdrawal;

  /// No description provided for @enterThePromoCodeAndGetAGift.
  ///
  /// In en, this message translates to:
  /// **'Enter the promo code and get a gift'**
  String get enterThePromoCodeAndGetAGift;

  /// No description provided for @activate.
  ///
  /// In en, this message translates to:
  /// **'Activate'**
  String get activate;

  /// No description provided for @promoCodeActivationFailed.
  ///
  /// In en, this message translates to:
  /// **'Promo code activation failed'**
  String get promoCodeActivationFailed;

  /// No description provided for @thePromoCodeHasBeenSuccessfullyActivatedYouHaveBeenCreditedWithFreeBet.
  ///
  /// In en, this message translates to:
  /// **'The promo code has been successfully activated. You have been credited with {creditAmount}₾ free bet.'**
  String thePromoCodeHasBeenSuccessfullyActivatedYouHaveBeenCreditedWithFreeBet(
    Object creditAmount,
  );

  /// No description provided for @play.
  ///
  /// In en, this message translates to:
  /// **'Play'**
  String get play;

  /// No description provided for @promoCodeCannotBeEmpty.
  ///
  /// In en, this message translates to:
  /// **'Promo code cannot be empty.'**
  String get promoCodeCannotBeEmpty;

  /// No description provided for @unexpectedErrorWhileLogginIn.
  ///
  /// In en, this message translates to:
  /// **'Unexpected error while loggin in'**
  String get unexpectedErrorWhileLogginIn;

  /// No description provided for @youCanFavoriteYourFavoriteSlotsByClickingOnTheStarInTheTopRightCorner.
  ///
  /// In en, this message translates to:
  /// **'You can favorite your favorite slots by clicking on the star in the top right corner.'**
  String
  get youCanFavoriteYourFavoriteSlotsByClickingOnTheStarInTheTopRightCorner;

  /// No description provided for @youCantParticipateInFantasy.
  ///
  /// In en, this message translates to:
  /// **'You can\'t participate in fantasy'**
  String get youCantParticipateInFantasy;

  /// No description provided for @returnToTheMainPage.
  ///
  /// In en, this message translates to:
  /// **'Return to the main page'**
  String get returnToTheMainPage;

  /// No description provided for @mainPage.
  ///
  /// In en, this message translates to:
  /// **'Main Page'**
  String get mainPage;

  /// No description provided for @manageNotifications.
  ///
  /// In en, this message translates to:
  /// **'Manage notifications'**
  String get manageNotifications;

  /// No description provided for @iWantAnSmsCodeToEnterInTheSystem.
  ///
  /// In en, this message translates to:
  /// **'I want an SMS code to enter in the system'**
  String get iWantAnSmsCodeToEnterInTheSystem;

  /// No description provided for @iWantSmsAboutWonTicket.
  ///
  /// In en, this message translates to:
  /// **'I want SMS about won ticket'**
  String get iWantSmsAboutWonTicket;

  /// No description provided for @receiveUpdatesOnPromotionsAndBonuses.
  ///
  /// In en, this message translates to:
  /// **'Receive updates on promotions and bonuses. Consent can be withdrawn anytime.'**
  String get receiveUpdatesOnPromotionsAndBonuses;

  /// No description provided for @unexpectedProblemWhileOpeningUpdateUrl.
  ///
  /// In en, this message translates to:
  /// **'Unexpected problem while opening update url'**
  String get unexpectedProblemWhileOpeningUpdateUrl;

  /// No description provided for @theFaCodeHasBeenSentToYourPhoneNumber.
  ///
  /// In en, this message translates to:
  /// **'The 2FA code has been sent to your phone number'**
  String get theFaCodeHasBeenSentToYourPhoneNumber;

  /// No description provided for @unexpectedErrorWhileStartingTheDepositFlow.
  ///
  /// In en, this message translates to:
  /// **'Unexpected error while starting the deposit flow'**
  String get unexpectedErrorWhileStartingTheDepositFlow;

  /// No description provided for @balanceFillUpRejected.
  ///
  /// In en, this message translates to:
  /// **'Balance fill up rejected'**
  String get balanceFillUpRejected;

  /// No description provided for @unexpectedErrorWhileDeletingTheCard.
  ///
  /// In en, this message translates to:
  /// **'Unexpected error while deleting the card'**
  String get unexpectedErrorWhileDeletingTheCard;

  /// No description provided for @recommended.
  ///
  /// In en, this message translates to:
  /// **'Recommended'**
  String get recommended;

  /// No description provided for @failedToLoadGames.
  ///
  /// In en, this message translates to:
  /// **'Failed to load games'**
  String get failedToLoadGames;

  /// No description provided for @topSlots.
  ///
  /// In en, this message translates to:
  /// **'Top Slots'**
  String get topSlots;
}

class _FuzzystarterLocalizationsDelegate
    extends LocalizationsDelegate<FuzzystarterLocalizations> {
  const _FuzzystarterLocalizationsDelegate();

  @override
  Future<FuzzystarterLocalizations> load(Locale locale) {
    return SynchronousFuture<FuzzystarterLocalizations>(
      lookupFuzzystarterLocalizations(locale),
    );
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ka'].contains(locale.languageCode);

  @override
  bool shouldReload(_FuzzystarterLocalizationsDelegate old) => false;
}

FuzzystarterLocalizations lookupFuzzystarterLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return FuzzystarterLocalizationsEn();
    case 'ka':
      return FuzzystarterLocalizationsKa();
  }

  throw FlutterError(
    'FuzzystarterLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
