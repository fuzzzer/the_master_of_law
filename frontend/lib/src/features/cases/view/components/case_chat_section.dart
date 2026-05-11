import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// In-case AI chat section — fully functional.
/// Persists conversation across tab switches. Uses case_intake mode
/// so AI asks clarifying questions. Offers "Build Case" when ready.
class CaseChatSection extends StatefulWidget {
  const CaseChatSection({super.key, required this.caseId});
  final String caseId;

  @override
  State<CaseChatSection> createState() => _CaseChatSectionState();
}

class _CaseChatSectionState extends State<CaseChatSection> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  late final ConsultationCubit _cubit;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _cubit = ConsultationCubit(
      repository: ConsultationRepository(
        remoteDataSource: ConsultationRemoteDataSource(),
      ),
      isCaseChat: true,
    );
    _initConversation();
  }

  Future<void> _initConversation() async {
    final caseDetailCubit = context.read<CaseDetailCubit>();
    final caseData = caseDetailCubit.state.caseData;

    // If case already has a linked conversation, try loading it
    if (caseData != null && caseData.linkedConversationIds.isNotEmpty) {
      final lastConvId = caseData.linkedConversationIds.last;
      await _cubit.loadConversation(lastConvId);

      // Fallback: if load failed (conversation deleted server-side), create fresh
      if (_cubit.state.status.isFailed) {
        _cubit.reset();
        await _createAndLinkConversation(caseDetailCubit);
      }
    } else {
      await _createAndLinkConversation(caseDetailCubit);
    }
    if (mounted) {
      final caseData = caseDetailCubit.state.caseData;
      final serverId = caseData?.serverCaseFileId;
      if (serverId != null && serverId.isNotEmpty) {
        _cubit.enterAgentMode(caseFileId: serverId);
      } else if (caseData != null && caseData.facts.isNotEmpty) {
        _tryResolveServerCaseFileId();
      }
      setState(() => _initialized = true);
    }
  }

  Future<void> _createAndLinkConversation(CaseDetailCubit caseDetailCubit) async {
    await _cubit.startConversation(caseId: widget.caseId);
    final convId = _cubit.state.conversationId;
    if (convId != null && convId.isNotEmpty) {
      caseDetailCubit.linkConversation(convId);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _cubit.close();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _cubit.sendMessage(text);
    _controller.clear();
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 200), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _buildCase() async {
    final caseFileData = await _cubit.buildCaseFile();
    if (caseFileData != null && mounted) {
      context.read<CaseDetailCubit>().populateFromAiAnalysis(caseFileData);
      final serverId = caseFileData['id']?.toString();
      
      final fullText = caseFileData['full_analysis_text']?.toString();
      if (fullText != null && fullText.isNotEmpty) {
        final aiMsg = ChatMessage(
          id: 'analysis_${DateTime.now().millisecondsSinceEpoch}',
          text: fullText,
          isUser: false,
          timestamp: DateTime.now(),
        );
        _cubit.injectMessage(aiMsg);
      }

      if (serverId != null) {
        _cubit.enterAgentMode(caseFileId: serverId);
        setState(() {});
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ საქმის სექციები შეივსო AI-ის ანალიზით')),
        );
        _scrollToBottom();
      }
    }
  }

  Future<void> _tryResolveServerCaseFileId() async {
    final convId = _cubit.state.conversationId;
    if (convId == null) return;
    try {
      final dataSource = ConsultationRemoteDataSource();
      final caseFiles = await dataSource.listCaseFiles();
      final match = (caseFiles as List?)?.firstWhere(
        (cf) => cf['conversation_id'] == convId,
        orElse: () => null,
      );
      if (match != null && mounted) {
        final serverId = match['id']?.toString();
        if (serverId != null) {
          context.read<CaseDetailCubit>().state.caseData?.serverCaseFileId = serverId;
          _cubit.enterAgentMode(caseFileId: serverId);
          setState(() {});
        }
      }
    } catch (_) {}
  }

  Future<void> _toggleAgentMode() async {
    if (_cubit.state.isAgentMode) {
      _cubit.exitAgentMode();
      setState(() {});
      return;
    }
    var serverId = context.read<CaseDetailCubit>().state.caseData?.serverCaseFileId;
    if (serverId == null) {
      await _tryResolveServerCaseFileId();
      if (!mounted) return;
      serverId = context.read<CaseDetailCubit>().state.caseData?.serverCaseFileId;
    }
    if (serverId != null && mounted) {
      _cubit.enterAgentMode(caseFileId: serverId);
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return BlocProvider.value(
      value: _cubit,
      child: Column(
        children: [
          // Context banner — reactive to agent mode
          BlocBuilder<ConsultationCubit, ConsultationState>(
            bloc: _cubit,
            buildWhen: (prev, curr) => prev.caseFileId != curr.caseFileId,
            builder: (context, consultState) {
              final caseData = context.read<CaseDetailCubit>().state.caseData;
              final hasBuiltCase =
                  caseData != null && (caseData.serverCaseFileId != null || caseData.facts.any((f) => f.isAiGenerated));
              final hasAgent = consultState.isAgentMode || hasBuiltCase;

              return Container(
                margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: consultState.isAgentMode
                      ? uiColors.accentColor.withValues(alpha: 0.08)
                      : uiColors.backgroundSecondaryColor,
                  borderRadius: BorderRadius.circular(12),
                  border: consultState.isAgentMode
                      ? Border.all(color: uiColors.accentColor.withValues(alpha: 0.3))
                      : null,
                ),
                child: hasAgent
                    ? Row(
                        children: [
                          Expanded(
                            child: GestureDetector(
                              onTap: consultState.isAgentMode ? _toggleAgentMode : null,
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                decoration: BoxDecoration(
                                  color: !consultState.isAgentMode
                                      ? uiColors.accentColor.withValues(alpha: 0.12)
                                      : Colors.transparent,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      Icons.chat_bubble_outline,
                                      size: 14,
                                      color: !consultState.isAgentMode
                                          ? uiColors.accentColor
                                          : uiColors.secondaryTextColor,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'ჩატი',
                                      style: uiTextStyles.labelBold12.copyWith(
                                        color: !consultState.isAgentMode
                                            ? uiColors.accentColor
                                            : uiColors.secondaryTextColor,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          Container(
                            width: 1,
                            height: 24,
                            color: uiColors.secondaryTextColor.withValues(alpha: 0.2),
                          ),
                          Expanded(
                            child: GestureDetector(
                              onTap: !consultState.isAgentMode ? _toggleAgentMode : null,
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                decoration: BoxDecoration(
                                  color: consultState.isAgentMode
                                      ? uiColors.accentColor.withValues(alpha: 0.15)
                                      : Colors.transparent,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      Icons.smart_toy,
                                      size: 14,
                                      color: consultState.isAgentMode
                                          ? uiColors.accentColor
                                          : uiColors.secondaryTextColor,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      '🤖 აგენტი',
                                      style: uiTextStyles.labelBold12.copyWith(
                                        color: consultState.isAgentMode
                                            ? uiColors.accentColor
                                            : uiColors.secondaryTextColor,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      )
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.folder_open, size: 16, color: uiColors.accentColor),
                          const SizedBox(width: 8),
                          Text(
                            'AI-ს აქვს საქმის სრული კონტექსტი',
                            style: uiTextStyles.labelBold12.copyWith(
                              color: uiColors.secondaryTextColor,
                            ),
                          ),
                        ],
                      ),
              );
            },
          ),

          // Messages
          Expanded(
            child: BlocConsumer<ConsultationCubit, ConsultationState>(
              listenWhen: (prev, curr) => prev.messages.length != curr.messages.length,
              listener: (context, state) {
                _scrollToBottom();
              },
              builder: (context, state) {
                if (!_initialized || (state.status.isLoading && state.messages.isEmpty)) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.psychology, size: 64, color: uiColors.accentColor.withValues(alpha: 0.4)),
                        const SizedBox(height: 20),
                        Text(
                          'AI კონსულტაცია',
                          style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'კავშირი მყარდება...',
                          style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2, color: uiColors.accentColor),
                        ),
                      ],
                    ),
                  );
                }

                if (state.status.isFailed && state.messages.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.cloud_off, size: 64, color: uiColors.errorColor.withValues(alpha: 0.5)),
                          const SizedBox(height: 20),
                          Text(
                            'კავშირი ვერ მოხერხდა',
                            style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _failureMessageKa(state.failureType),
                            style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: _initConversation,
                            icon: const Icon(Icons.refresh, size: 18),
                            label: const Text('ხელახლა ცდა'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: uiColors.accentColor,
                              foregroundColor: uiColors.backgroundPrimaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                if (state.messages.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.psychology, size: 64, color: uiColors.accentColor.withValues(alpha: 0.4)),
                        const SizedBox(height: 20),
                        Text(
                          'AI კონსულტაცია',
                          style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'აღწერეთ თქვენი სიტუაცია და AI დაგისვამთ\nდამაზუსტებელ კითხვებს.',
                          style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  itemCount:
                      state.messages.length +
                      (state.isSending ? 1 : 0) +
                      (state.caseAnalysisReady && !state.isBuildingCase ? 1 : 0),
                  itemBuilder: (context, index) {
                    // Typing indicator
                    if (index == state.messages.length && state.isSending) {
                      return _TypingIndicator(uiColors: uiColors, uiTextStyles: uiTextStyles);
                    }

                    // Case analysis ready CTA
                    if (index == state.messages.length + (state.isSending ? 1 : 0) &&
                        state.caseAnalysisReady &&
                        !state.isBuildingCase) {
                      final caseData = context.read<CaseDetailCubit>().state.caseData;
                      final hasBuiltCase = caseData != null &&
                          (caseData.serverCaseFileId != null || caseData.facts.any((f) => f.isAiGenerated));

                      return _BuildCaseCta(
                        uiColors: uiColors,
                        uiTextStyles: uiTextStyles,
                        onBuild: _buildCase,
                        isBuilding: state.isBuildingCase,
                        isRegenerate: hasBuiltCase,
                      );
                    }

                    if (index >= state.messages.length) return const SizedBox.shrink();

                    final msg = state.messages[index];
                    return _MessageBubble(message: msg, uiColors: uiColors, uiTextStyles: uiTextStyles);
                  },
                );
              },
            ),
          ),

          // Building indicator
          BlocBuilder<ConsultationCubit, ConsultationState>(
            buildWhen: (prev, curr) => prev.isBuildingCase != curr.isBuildingCase,
            builder: (context, state) {
              if (!state.isBuildingCase) return const SizedBox.shrink();
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                color: uiColors.accentColor.withValues(alpha: 0.1),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: uiColors.accentColor),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'საქმის ანალიზი მიმდინარეობს...',
                      style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor),
                    ),
                  ],
                ),
              );
            },
          ),

          // Input bar
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: uiColors.backgroundSecondaryColor,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: uiColors.secondaryTextColor.withValues(alpha: 0.15)),
              ),
              child: Row(
                children: [
                  BlocBuilder<ConsultationCubit, ConsultationState>(
                    builder: (builderContext, state) {
                      return IconButton(
                        icon: Icon(Icons.auto_awesome, color: uiColors.accentColor),
                        tooltip: 'საქმის შევსება',
                        onPressed: state.isBuildingCase ? null : _buildCase,
                      );
                    },
                  ),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _send(),
                      decoration: InputDecoration(
                        hintText: 'აღწერეთ სიტუაცია...',
                        hintStyle: uiTextStyles.body14.copyWith(
                          color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: _send,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(color: uiColors.accentColor, shape: BoxShape.circle),
                      child: Icon(Icons.arrow_upward, color: uiColors.backgroundPrimaryColor, size: 20),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// CTA button shown when AI has gathered enough info.
class _BuildCaseCta extends StatefulWidget {
  const _BuildCaseCta({
    required this.uiColors,
    required this.uiTextStyles,
    required this.onBuild,
    required this.isBuilding,
    this.isRegenerate = false,
  });
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onBuild;
  final bool isBuilding;
  final bool isRegenerate;

  @override
  State<_BuildCaseCta> createState() => _BuildCaseCtaState();
}

class _BuildCaseCtaState extends State<_BuildCaseCta> {
  late bool _expanded = !widget.isRegenerate;

  @override
  void didUpdateWidget(covariant _BuildCaseCta oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isRegenerate != oldWidget.isRegenerate) {
      _expanded = !widget.isRegenerate;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_expanded) {
      return GestureDetector(
        onTap: () => setState(() => _expanded = true),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 12),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: widget.uiColors.accentColor.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: widget.uiColors.accentColor.withValues(alpha: 0.3)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.auto_awesome, size: 16, color: widget.uiColors.accentColor),
              const SizedBox(width: 8),
              Text(
                'საქმის ხელახლა გენერაცია',
                style: widget.uiTextStyles.bodyBold14.copyWith(color: widget.uiColors.accentColor),
              ),
              const SizedBox(width: 4),
              Icon(Icons.expand_more, size: 16, color: widget.uiColors.accentColor),
            ],
          ),
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: widget.uiColors.accentColor.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: widget.uiColors.accentColor.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.isRegenerate) const SizedBox(width: 24), // balance for expand_less icon
              Expanded(
                child: Text(
                  widget.isRegenerate ? '🔄 განახლებული ინფორმაცია ხელმისაწვდომია' : '✅ AI-მ საკმარისი ინფორმაცია შეაგროვა',
                  style: widget.uiTextStyles.bodyBold14.copyWith(color: widget.uiColors.accentColor),
                  textAlign: TextAlign.center,
                ),
              ),
              if (widget.isRegenerate)
                GestureDetector(
                  onTap: () => setState(() => _expanded = false),
                  child: Padding(
                    padding: const EdgeInsets.only(left: 4),
                    child: Icon(Icons.expand_less, size: 20, color: widget.uiColors.accentColor),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: widget.isBuilding ? null : widget.onBuild,
              icon: const Icon(Icons.auto_awesome, size: 18),
              label: Text(widget.isRegenerate ? '🔄 საქმის ხელახლა გენერაცია' : '📁 საქმის ანალიზის გენერაცია'),
              style: ElevatedButton.styleFrom(
                backgroundColor: widget.uiColors.accentColor,
                foregroundColor: widget.uiColors.backgroundPrimaryColor,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Single chat message bubble.
class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message, required this.uiColors, required this.uiTextStyles});
  final ChatMessage message;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser
              ? uiColors.accentColor.withValues(alpha: 0.15)
              : message.isError
              ? uiColors.errorColor.withValues(alpha: 0.1)
              : uiColors.surfaceColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
            bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
          ),
          border: message.isError ? Border.all(color: uiColors.errorColor.withValues(alpha: 0.3)) : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser && message.trustLevel != null) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _trustColor(message.trustLevel!).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  _trustLabel(message.trustLevel!),
                  style: uiTextStyles.caption11.copyWith(
                    color: _trustColor(message.trustLevel!),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
            SelectableText(
              message.isError && message.failureType != null ? _failureMessageKa(message.failureType) : message.text,
              style: uiTextStyles.body14.copyWith(
                color: message.isError ? uiColors.errorColor : uiColors.primaryTextColor,
                height: 1.5,
              ),
            ),
            if (message.citations != null && message.citations!.isNotEmpty) ...[
              const SizedBox(height: 12),
              ...message.citations!.map(
                (c) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: uiColors.backgroundPrimaryColor.withValues(alpha: 0.5),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.2)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.gavel, size: 12, color: uiColors.accentColor),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          c.articleTitle,
                          style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _trustColor(String level) => switch (level) {
    'verified' => const Color(0xFF2ECC71),
    'interpretation' => const Color(0xFFF39C12),
    _ => const Color(0xFF95A5A6),
  };

  String _trustLabel(String level) => switch (level) {
    'verified' => '✓ დადასტურებული',
    'interpretation' => '◐ ინტერპრეტაცია',
    _ => '○ ზოგადი მითითება',
  };
}

/// Typing indicator shown while AI is responding.
class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator({required this.uiColors, required this.uiTextStyles});
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: uiColors.surfaceColor,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
            bottomRight: Radius.circular(16),
            bottomLeft: Radius.circular(4),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: uiColors.accentColor),
            ),
            const SizedBox(width: 10),
            Text('AI ფიქრობს...', style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
          ],
        ),
      ),
    );
  }
}

String _failureMessageKa(ConsultationFailureType? type) => switch (type) {
  ConsultationFailureType.network => 'სერვერთან დაკავშირება ვერ მოხერხდა.\nშეამოწმეთ ინტერნეტ კავშირი.',
  ConsultationFailureType.unauthorized => 'სესია ვადაგასულია.\nგთხოვთ ხელახლა შეხვიდეთ.',
  ConsultationFailureType.noCredits => 'კრედიტები ამოიწურა.\nშეიძინეთ დამატებითი.',
  ConsultationFailureType.notFound => 'მოთხოვნილი რესურსი ვერ მოიძებნა.',
  ConsultationFailureType.serverError => 'სერვერის შეცდომა.\nგთხოვთ ცოტა მოგვიანებით სცადოთ.',
  ConsultationFailureType.unknown || null => 'უცნობი შეცდომა მოხდა.\nხელახლა სცადეთ.',
};
