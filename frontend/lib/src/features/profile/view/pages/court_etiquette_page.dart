import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

class CourtEtiquettePage extends StatelessWidget {
  const CourtEtiquettePage({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final rules = [
      'როდესაც მოსამართლე შემოდის სასამართლო დარბაზში, ყველა უნდა წამოდგეს.',
      'მოსამართლეს მიმართეთ პატივისცემით: "ბატონო მოსამართლევ" ან "ქალბატონო მოსამართლევ".',
      'ისაუბრეთ მხოლოდ მაშინ, როდესაც მოსამართლე მოგცემთ სიტყვას.',
      'არ შეაწყვეტინოთ საუბარი მოსამართლეს, მოწინააღმდეგე მხარეს ან მოწმეს.',
      'ჩაიცვით მოწესრიგებულად. სასურველია საქმიანი სტილის ტანსაცმელი.',
      'სასამართლო სხდომის დროს გამორთეთ მობილური ტელეფონი ან გადაიყვანეთ უხმო რეჟიმზე.',
      'დაუშვებელია სასამართლო დარბაზში საკვების ან სასმელის მიღება.',
      'აკონტროლეთ ემოციები. მოერიდეთ აგრესიულ ჟესტიკულაციას და ხმამაღალ საუბარს.',
      'პასუხები გაეცით გასაგებად და მიკროფონთან ახლოს, რადგან მიმდინარეობს აუდიო-ვიდეო ჩაწერა.',
    ];

    return Scaffold(
      // Title style comes from appBarTheme (titleM + ink), built from roles.
      appBar: AppBar(title: const Text('სასამართლო ეტიკეტი')),
      body: ListView.separated(
        padding: density.screen,
        itemCount: rules.length,
        separatorBuilder: (context, index) => SizedBox(height: space.m),
        itemBuilder: (context, index) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                margin: EdgeInsets.only(top: space.xs, right: space.m),
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: colors.ink,
                  borderRadius: BorderRadius.circular(radius.circle),
                ),
              ),
              Expanded(
                child: Text(
                  rules[index],
                  style: type.body.copyWith(color: colors.ink),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
