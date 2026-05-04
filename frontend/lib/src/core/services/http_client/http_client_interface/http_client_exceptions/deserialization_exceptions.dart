class DeserializationException implements Exception {
  final Object? error;
  final String? message;

  const DeserializationException({this.error, this.message});

  @override
  String toString() => 'JsonDeserializationException(error: $error, message: $message})';
}

class JsonDeserializationException extends DeserializationException {
  const JsonDeserializationException({super.error, super.message});
}
