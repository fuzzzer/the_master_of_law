import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

class CourtEtiquettePage extends StatelessWidget {
  const CourtEtiquettePage({super.key});

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

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
      appBar: AppBar(
        title: Text(
          'სასამართლო ეტიკეტი',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: rules.length,
        separatorBuilder: (context, index) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                margin: const EdgeInsets.only(top: 4, right: 12),
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: uiColors.accentColor,
                  shape: BoxShape.circle,
                ),
              ),
              Expanded(
                child: Text(
                  rules[index],
                  style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
