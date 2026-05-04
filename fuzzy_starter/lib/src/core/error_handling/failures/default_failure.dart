import 'package:flutter/material.dart';

@immutable
class DefaultFailure {
  final Type? type;
  final String? message;
  final String? internalMessage;
  final int? errorCode;

  const DefaultFailure({
    this.type,
    required this.message,
    this.internalMessage,
    this.errorCode,
  });

  const DefaultFailure.empty() : type = Exception, message = '', internalMessage = '', errorCode = null;

  @override
  String toString() =>
      'Failure('
      'type: $type, '
      'message: $message, '
      'internalMessage: $internalMessage, '
      'errorCode: $errorCode'
      ')';

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is DefaultFailure &&
        other.type == type &&
        other.message == message &&
        other.internalMessage == internalMessage &&
        other.errorCode == errorCode;
  }

  @override
  int get hashCode => type.hashCode ^ message.hashCode ^ internalMessage.hashCode ^ errorCode.hashCode;
}
