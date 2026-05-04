import 'package:flutter/material.dart';

enum ActionStateStatus {
  initial,
  loading,
  success,
  actionVerificationRequired,
  failed;

  bool get isInitial => this == ActionStateStatus.initial;
  bool get isLoading => this == ActionStateStatus.loading;
  bool get isSuccess => this == ActionStateStatus.success;
  bool get isActionVerificationRequired => this == ActionStateStatus.actionVerificationRequired;
  bool get isFailed => this == ActionStateStatus.failed;
}

class ActionStatusBuilder {
  ActionStatusBuilder._();

  static Widget buildByStatus({
    required ActionStateStatus actionStatus,
    required Widget Function() onInitial,
    required Widget Function() onLoading,
    required Widget Function() onSuccess,
    required Widget Function() onActionVerificationRequired,
    required Widget Function()? onFailure,
  }) {
    if (actionStatus == ActionStateStatus.initial) {
      return onInitial();
    }

    if (actionStatus == ActionStateStatus.loading) {
      return onLoading();
    }

    if (actionStatus == ActionStateStatus.success) {
      return onSuccess();
    }

    if (actionStatus == ActionStateStatus.actionVerificationRequired) {
      return onActionVerificationRequired();
    }

    if (actionStatus == ActionStateStatus.failed && onFailure != null) {
      return onFailure();
    }

    return Container();
  }
}
