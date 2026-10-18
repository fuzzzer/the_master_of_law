import json

with open('frontend/assets/json/legal_dictionary.json', 'r', encoding='utf-8') as f:
    terms = json.load(f)

dart_content = """import 'package:flutter/material.dart';

class LegalTerm {
  final String term;
  final String definition;

  const LegalTerm({required this.term, required this.definition});
}

const List<LegalTerm> legalDictionaryData = [
"""

for t in terms:
    term = t['term'].replace("'", "\\'")
    definition = t['definition'].replace("'", "\\'")
    dart_content += f"  LegalTerm(term: '{term}', definition: '{definition}'),\n"

dart_content += "];\n"

with open('frontend/lib/src/features/profile/view/pages/legal_dictionary_data.dart', 'w', encoding='utf-8') as f:
    f.write(dart_content)

