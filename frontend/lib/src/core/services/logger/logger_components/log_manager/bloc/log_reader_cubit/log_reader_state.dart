part of 'log_reader_cubit.dart';

class LogReaderState {
  final StateStatus status;
  final List<String>? logRecordList;
  final DefaultFailure? failure;

  const LogReaderState({
    required this.status,
    this.logRecordList,
    this.failure,
  });

  LogReaderState copyWith({
    StateStatus? status,
    List<String>? logRecordList,
    DefaultFailure? failure,
  }) {
    return LogReaderState(
      status: status ?? this.status,
      logRecordList: logRecordList ?? this.logRecordList,
      failure: failure ?? this.failure,
    );
  }

  @override
  String toString() => 'LoggerReaderState(status: $status, logRecord: $logRecordList, failure: $failure)';
}
