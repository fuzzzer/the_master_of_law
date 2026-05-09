import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:url_launcher/url_launcher.dart';

class UsefulContactsPage extends StatelessWidget {
  const UsefulContactsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    final contacts = [
      {
        'title': 'იურიდიული დახმარების სამსახური',
        'subtitle': 'უფასო საადვოკატო მომსახურება',
        'phone': '1485',
      },
      {
        'title': 'საქართველოს სახალხო დამცველი',
        'subtitle': 'ადამიანის უფლებათა დაცვა',
        'phone': '1481',
      },
      {
        'title': 'საქართველოს ახალგაზრდა იურისტთა ასოციაცია (GYLA)',
        'subtitle': 'უფასო იურიდიული კონსულტაცია',
        'phone': '032 293 61 01',
      },
      {
        'title': 'შინაგან საქმეთა სამინისტრო',
        'subtitle': 'გადაუდებელი დახმარება',
        'phone': '112',
      },
      {
        'title': 'გენერალური ინსპექცია',
        'subtitle': 'პოლიციის მხრიდან დარღვევებზე',
        'phone': '126',
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'სასარგებლო კონტაქტები',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: contacts.length,
        separatorBuilder: (context, index) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final contact = contacts[index];
          final phone = contact['phone']!;
          final dialNumber = phone.replaceAll(' ', '');

          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: uiColors.backgroundSecondaryColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contact['title']!,
                  style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
                ),
                const SizedBox(height: 4),
                Text(
                  contact['subtitle']!,
                  style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                ),
                const SizedBox(height: 12),
                GestureDetector(
                  onTap: () => launchUrl(Uri(scheme: 'tel', path: dialNumber)),
                  onLongPress: () {
                    Clipboard.setData(ClipboardData(text: phone));
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('$phone დაკოპირებულია'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                  child: Row(
                    children: [
                      Icon(Icons.phone, size: 16, color: uiColors.accentColor),
                      const SizedBox(width: 8),
                      Text(
                        phone,
                        style: uiTextStyles.bodyBold14.copyWith(
                          color: uiColors.accentColor,
                          decoration: TextDecoration.underline,
                          decorationColor: uiColors.accentColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
