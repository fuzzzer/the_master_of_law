import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:url_launcher/url_launcher.dart';

class UsefulContactsPage extends StatelessWidget {
  const UsefulContactsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

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
      // Title style comes from appBarTheme (titleM + ink), built from roles.
      appBar: AppBar(title: const Text('სასარგებლო კონტაქტები')),
      body: ListView.separated(
        padding: density.screen,
        itemCount: contacts.length,
        separatorBuilder: (context, index) => SizedBox(height: space.m),
        itemBuilder: (context, index) {
          final contact = contacts[index];
          final phone = contact['phone']!;
          final dialNumber = phone.replaceAll(' ', '');

          return Container(
            padding: density.card,
            decoration: BoxDecoration(
              color: colors.surface,
              border: Border.all(color: colors.line),
              borderRadius: BorderRadius.circular(radius.l),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contact['title']!,
                  style: type.titleS.copyWith(color: colors.ink),
                ),
                SizedBox(height: space.xs),
                Text(
                  contact['subtitle']!,
                  style: type.bodyS.copyWith(color: colors.inkMute),
                ),
                SizedBox(height: space.m),
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => launchUrl(Uri(scheme: 'tel', path: dialNumber)),
                  onLongPress: () {
                    Clipboard.setData(ClipboardData(text: phone));
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('$phone დაკოპირებულია'),
                        // Dwell time, not animation: the kit's longest motion
                        // role is `pulse` at 1600ms. Becomes FuzzzyToast's own
                        // dwell at M11 — see JOURNAL M3.
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                  child: Row(
                    children: [
                      Icon(Icons.phone, size: 16, color: colors.ink),
                      SizedBox(width: space.s),
                      Text(
                        phone,
                        style: type.titleS.copyWith(
                          color: colors.ink,
                          decoration: TextDecoration.underline,
                          decorationColor: colors.ink,
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
