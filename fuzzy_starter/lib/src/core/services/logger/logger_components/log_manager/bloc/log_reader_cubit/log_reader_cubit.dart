import 'package:bloc/bloc.dart';
import 'package:fuzzystarter/src/src.dart';

part 'log_reader_state.dart';

class LogReaderCubit extends Cubit<LogReaderState> {
  LogReaderCubit({required this.logStorageService})
    : super(
        const LogReaderState(status: StateStatus.initial),
      );

  final LogStorageService logStorageService;

  Future<void> getLogs() async {
    emit(state.copyWith(status: StateStatus.loading));
    try {
      final List<String> logs = await logStorageService.readLogs();

      emit(state.copyWith(status: StateStatus.success, logRecordList: logs));
    } catch (ex) {
      logger.e('message $ex');
      emit(
        state.copyWith(
          status: StateStatus.failed,
          failure: DefaultFailure(
            message: ex.toString(),
          ),
        ),
      );
    }
  }
}
