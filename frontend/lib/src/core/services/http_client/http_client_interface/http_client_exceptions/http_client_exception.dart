class HttpClientException implements Exception {
  final String? uri;
  final String? message;

  HttpClientException({this.uri, this.message});

  @override
  String toString() => 'HttpClientException(uri: $uri, message: $message)';
}
