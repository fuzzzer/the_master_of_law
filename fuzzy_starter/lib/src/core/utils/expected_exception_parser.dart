import '../../src.dart';

T parseWithExpectedDeserializationException<T>({required T Function() parser}) {
  try {
    return parser();
  } catch (ex) {
    logger.e(ex);

    throw JsonDeserializationException(
      error: ex,
      message: 'JsonDeserializationException while parsing ${T.runtimeType} }',
    );
  }
}
