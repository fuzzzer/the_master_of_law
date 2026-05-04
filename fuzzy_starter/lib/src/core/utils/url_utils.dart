String appendQueryParameter(String url, String key, String value) {
  final uri = Uri.parse(url);
  final newQueryParameters = Map<String, String>.from(uri.queryParameters);
  newQueryParameters[key] = value;
  return uri.replace(queryParameters: newQueryParameters).toString();
}