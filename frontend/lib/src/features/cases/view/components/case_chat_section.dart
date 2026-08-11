import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:url_launcher/url_launcher.dart';

/// In-case AI chat section — unified advocate.
/// Persists conversation across tab switches. When case_file_id is available,
/// AI automatically uses tools (add_fact, link_article, etc.) via WebSocket.
///
/// This is the SECOND chat surface in the app; `consultation_page.dart` (M6b)
/// is the first. Every shared idiom here — the bubble geometry, the citation
/// chip, the docked composer, the typing box — is deliberately the same shape
/// as its twin there, so the two chats read as one product and M11 can swap
/// both onto `FuzzzyChatBubble` in one move.
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
      // Auto-set case file ID so tools are available via unified WebSocket
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

  Future<void> _createAndLinkConversation(
    CaseDetailCubit caseDetailCubit,
  ) async {
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
    // The 200ms is a SETTLE, not animation timing: it lets the freshly
    // appended row lay out before we read `maxScrollExtent`. `motion.*` is for
    // things the user watches move, and the guard's `literal-motion` rule
    // (which matches the named argument `duration:`) correctly does not fire
    // on a `Future.delayed` positional. The scroll itself IS watched, so it
    // takes `motion.standard` / `standardCurve`.
    Future.delayed(const Duration(milliseconds: 200), () {
      if (!mounted || !_scrollController.hasClients) return;
      final motion = context.fuzzzyMotion;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: motion.standard,
        curve: motion.standardCurve,
      );
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
        // M11: the leading '✅' is DROPPED rather than re-iconified — the
        // toast's `success` kind already carries that exact meaning in its
        // 3px left rule, so the emoji was a second copy of one signal.
        FuzzzyToast.show(
          context,
          message: 'საქმის სექციები შეივსო დამხმარის ანალიზით',
          kind: FuzzzyToastKind.success,
          qaId: 'caseChat.sectionsFilled',
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
      final match = caseFiles.cast<Map<String, dynamic>>().firstWhereOrNull(
        (cf) => cf['conversation_id'] == convId,
      );
      if (match != null && mounted) {
        final serverId = match['id']?.toString();
        if (serverId != null) {
          context.read<CaseDetailCubit>().state.caseData?.serverCaseFileId =
              serverId;
          _cubit.enterAgentMode(caseFileId: serverId);
          setState(() {});
        }
      }
    } catch (e, st) {
      // Tool wiring is best-effort; log so silent failures are diagnosable.
      logger.e(
        'Failed to resolve server case file id',
        error: e,
        stackTrace: st,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return BlocProvider.value(
      value: _cubit,
      child: Column(
        children: [
          // Context banner — shows AI capabilities
          BlocBuilder<ConsultationCubit, ConsultationState>(
            bloc: _cubit,
            buildWhen: (prev, curr) =>
                prev.caseFileId != curr.caseFileId ||
                prev.streamingStatus != curr.streamingStatus,
            builder: (context, consultState) {
              final hasTools = consultState.isAgentMode;
              final statusText = consultState.streamingStatus;

              return Container(
                margin: EdgeInsets.fromLTRB(space.l, space.m, space.l, 0),
                padding: density.notice,
                // MAPPING §2.2 judgement 2: the tools-on state was a gold panel
                // at alpha 0.08 with a gold border at 0.3; the tools-off state
                // was a plain `backgroundSecondary` panel with NO border at
                // all. In Ink those are ONE rung — both are `surface` — so what
                // separated them (a hue) is gone and what separates them now is
                // the border weight plus the ink rung. Same idiom M8 gave
                // `_AiConsultationCard`. The tools-off state also GAINS the
                // `line` hairline it never had, without which a `surface` box
                // on `ground` is nearly invisible.
                decoration: BoxDecoration(
                  color: colors.surface,
                  borderRadius: BorderRadius.circular(radius.m),
                  border: Border.all(
                    color: hasTools ? colors.lineStrong : colors.line,
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      hasTools ? Icons.auto_awesome : Icons.chat_bubble_outline,
                      // Dimension: the inline glyph, sized to the one-line
                      // notice it shares a row with.
                      size: 14,
                      color: hasTools ? colors.ink : colors.inkMute,
                    ),
                    SizedBox(width: space.s),
                    Flexible(
                      child: Text(
                        statusText ??
                            (hasTools
                                ? 'დამხმარე ავტომატურად აკეთებს საქმის ცვლილებებს'
                                : 'დამხმარეს აქვს საქმის სრული კონტექსტი'),
                        style: type.control.copyWith(
                          color: hasTools ? colors.ink : colors.inkMute,
                        ),
                        overflow: TextOverflow.ellipsis,
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
              listenWhen: (prev, curr) =>
                  prev.messages.length != curr.messages.length,
              listener: (context, state) {
                _scrollToBottom();
              },
              builder: (context, state) {
                if (!_initialized ||
                    (state.status.isLoading && state.messages.isEmpty)) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Dimension: the oversized empty-state glyph. All of
                        // MoL's 48/64px state glyphs were unified on `inkFaint`
                        // at M4 — at this size a semantic hue is a decorative
                        // wash, and the headline below names the state.
                        Icon(
                          Icons.psychology,
                          size: 64,
                          color: colors.inkFaint,
                        ),
                        SizedBox(height: space.l),
                        Text(
                          'დამხმარე კონსულტაცია',
                          style: type.titleM.copyWith(color: colors.ink),
                        ),
                        SizedBox(height: space.s),
                        Text(
                          'კავშირი მყარდება...',
                          style: type.body.copyWith(color: colors.inkMute),
                        ),
                        SizedBox(height: space.l),
                        const SizedBox(
                          // Dimension: the in-flow spinner's own footprint.
                          width: 24,
                          height: 24,
                          child: _Spinner(),
                        ),
                      ],
                    ),
                  );
                }

                if (state.status.isFailed && state.messages.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: EdgeInsets.all(space.xxl),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Same M4 rule as above: the 64px failure glyph is
                          // `inkFaint`, not `destructive`. The screen's red
                          // voice belongs to the error BUBBLES and the pending
                          // confirmation card, both of which are real markers.
                          Icon(
                            Icons.cloud_off,
                            size: 64,
                            color: colors.inkFaint,
                          ),
                          SizedBox(height: space.l),
                          Text(
                            'კავშირი ვერ მოხერხდა',
                            style: type.titleM.copyWith(color: colors.ink),
                          ),
                          SizedBox(height: space.s),
                          Text(
                            _failureMessageKa(state.failureType),
                            style: type.body.copyWith(color: colors.inkMute),
                            textAlign: TextAlign.center,
                          ),
                          SizedBox(height: space.xl),
                          ElevatedButton.icon(
                            onPressed: _initConversation,
                            icon: const Icon(Icons.refresh, size: 18),
                            label: const Text('ხელახლა ცდა'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: colors.actionPrimaryBg,
                              foregroundColor: colors.actionPrimaryFg,
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
                        Icon(
                          Icons.psychology,
                          size: 64,
                          color: colors.inkFaint,
                        ),
                        SizedBox(height: space.l),
                        Text(
                          'დამხმარე კონსულტაცია',
                          style: type.titleM.copyWith(color: colors.ink),
                        ),
                        SizedBox(height: space.s),
                        Text(
                          'აღწერეთ თქვენი სიტუაცია და დამხმარე დაგისვამთ\nდამაზუსტებელ კითხვებს.',
                          style: type.body.copyWith(color: colors.inkMute),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: EdgeInsets.symmetric(
                    horizontal: space.l,
                    vertical: space.m,
                  ),
                  itemCount:
                      state.messages.length +
                      (state.isSending ? 1 : 0) +
                      (state.caseAnalysisReady && !state.isBuildingCase
                          ? 1
                          : 0),
                  itemBuilder: (context, index) {
                    // Typing indicator
                    if (index == state.messages.length && state.isSending) {
                      return const _TypingIndicator();
                    }

                    // Case analysis ready CTA
                    if (index ==
                            state.messages.length + (state.isSending ? 1 : 0) &&
                        state.caseAnalysisReady &&
                        !state.isBuildingCase) {
                      final caseData = context
                          .read<CaseDetailCubit>()
                          .state
                          .caseData;
                      final hasBuiltCase =
                          caseData != null &&
                          (caseData.serverCaseFileId != null ||
                              caseData.facts.any((f) => f.isAiGenerated));

                      return _BuildCaseCta(
                        onBuild: _buildCase,
                        isBuilding: state.isBuildingCase,
                        isRegenerate: hasBuiltCase,
                      );
                    }

                    if (index >= state.messages.length) {
                      return const SizedBox.shrink();
                    }

                    final msg = state.messages[index];
                    return _MessageBubble(message: msg);
                  },
                );
              },
            ),
          ),

          // Building indicator
          BlocBuilder<ConsultationCubit, ConsultationState>(
            buildWhen: (prev, curr) =>
                prev.isBuildingCase != curr.isBuildingCase,
            builder: (context, state) {
              if (!state.isBuildingCase) return const SizedBox.shrink();
              return Container(
                padding: EdgeInsets.symmetric(
                  horizontal: space.l,
                  vertical: space.s,
                ),
                // The fork painted this strip with a bare `accentColor` at
                // alpha 0.1. It is the top rung of the docked stack, so it
                // takes `surface` and the `line` rule that separates the dock
                // from the scrolling list (USING §2.4 — no alpha tints).
                decoration: BoxDecoration(
                  color: colors.surface,
                  border: Border(top: BorderSide(color: colors.line)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(
                      // Dimension: the inline spinner's own footprint.
                      width: 16,
                      height: 16,
                      child: _Spinner(),
                    ),
                    SizedBox(width: space.s),
                    Text(
                      'საქმის ანალიზი მიმდინარეობს...',
                      style: type.control.copyWith(color: colors.ink),
                    ),
                  ],
                ),
              );
            },
          ),

          // Pending confirmations
          BlocBuilder<ConsultationCubit, ConsultationState>(
            buildWhen: (prev, curr) =>
                prev.pendingConfirmations != curr.pendingConfirmations,
            builder: (context, state) {
              if (state.pendingConfirmations.isEmpty) {
                return const SizedBox.shrink();
              }
              return Padding(
                padding: EdgeInsets.symmetric(horizontal: space.l),
                child: Column(
                  children: state.pendingConfirmations.map((pending) {
                    return _PendingConfirmationCard(
                      data: pending,
                      onConfirm: () =>
                          _cubit.confirmToolAction(pending.confirmationId!),
                      onReject: () =>
                          _cubit.rejectToolAction(pending.confirmationId!),
                    );
                  }).toList(),
                ),
              );
            },
          ),

          // Input bar — M6b's docked composer, verbatim.
          //
          // The fork wrapped the whole row (button + field + send disc) in a
          // 24px-radius pill Container that faked a fill, a border and a
          // radius, and then had to switch the TextField's OWN decoration off
          // (`border: InputBorder.none`, a local `hintStyle`, a local
          // `contentPadding`). RUN_BRIEF §4 forbids re-declaring field
          // decoration locally, so the pill is gone: the bar is now `surface`
          // with a `line` top rule, and the field opts INTO M1's
          // `inputDecorationTheme` (built from `FuzzzyFormStyles`) exactly as
          // `consultation_page._buildInputBar` does.
          Container(
            padding: EdgeInsets.fromLTRB(space.s, space.m, space.s, space.m),
            decoration: BoxDecoration(
              color: colors.surface,
              border: Border(top: BorderSide(color: colors.line)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                BlocBuilder<ConsultationCubit, ConsultationState>(
                  builder: (builderContext, state) {
                    return Padding(
                      padding: EdgeInsets.only(bottom: space.xs),
                      child: IconButton(
                        icon: Icon(
                          Icons.auto_awesome,
                          color: state.isBuildingCase
                              ? colors.inkFaint
                              : colors.ink,
                          // Dimension: matches the composer glyph in the
                          // consultation composer.
                          size: 22,
                        ),
                        tooltip: 'საქმის შევსება',
                        onPressed: state.isBuildingCase ? null : _buildCase,
                        visualDensity: VisualDensity.compact,
                      ),
                    );
                  },
                ),
                Expanded(
                  child: TextField(
                    controller: _controller,
                    style: type.body.copyWith(color: colors.fieldText),
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      hintText: 'აღწერეთ სიტუაცია...',
                    ),
                  ),
                ),
                SizedBox(width: space.s),
                Padding(
                  padding: EdgeInsets.only(bottom: space.xs),
                  child: FuzzzyHitTarget(
                    child: GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: _send,
                      child: Container(
                        // Dimension: the send affordance's own footprint. The
                        // 44×44 touch minimum is met by FuzzzyHitTarget
                        // WITHOUT growing the painted disc (M6b §D).
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: colors.actionPrimaryBg,
                          borderRadius: BorderRadius.circular(radius.circle),
                        ),
                        child: Icon(
                          Icons.arrow_upward,
                          color: colors.actionPrimaryFg,
                          // Dimension: the glyph inside the 40px disc.
                          size: 20,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// The in-flow progress spinner, on the content ink.
///
/// MAPPING §2.2 routes every `CircularProgressIndicator.color` to `ink` — a
/// spinner is content, not an action fill. Extracted so the three call sites
/// in this file cannot drift apart, and so the `strokeWidth` is documented
/// once rather than three times.
class _Spinner extends StatelessWidget {
  const _Spinner();

  @override
  Widget build(BuildContext context) {
    // Dimension: a 2px stroke is what reads at 16–24px. Not a `space` rung.
    return CircularProgressIndicator(
      strokeWidth: 2,
      color: context.fuzzzyColors.ink,
    );
  }
}

/// CTA button shown when AI has gathered enough info.
class _BuildCaseCta extends StatefulWidget {
  const _BuildCaseCta({
    required this.onBuild,
    required this.isBuilding,
    this.isRegenerate = false,
  });
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    // Both states were a gold panel at alpha 0.1 inside a gold border at 0.3.
    // M8's `_AiConsultationCard` call, repeated: a CTA card is a peer `surface`
    // card whose call-to-action-ness is carried by the one-step-heavier
    // `lineStrong` border and by the affordances inside it, never by a tint.
    final boxDecoration = BoxDecoration(
      color: colors.surface,
      borderRadius: BorderRadius.circular(radius.l),
      border: Border.all(color: colors.lineStrong),
    );

    if (!_expanded) {
      return GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => setState(() => _expanded = true),
        child: Container(
          margin: EdgeInsets.symmetric(vertical: space.m),
          padding: density.tile,
          decoration: boxDecoration,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.auto_awesome, size: 16, color: colors.ink),
              SizedBox(width: space.s),
              Text(
                'საქმის ხელახლა გენერაცია',
                style: type.titleS.copyWith(color: colors.ink),
              ),
              SizedBox(width: space.xs),
              Icon(Icons.expand_more, size: 16, color: colors.ink),
            ],
          ),
        ),
      );
    }

    return Container(
      margin: EdgeInsets.symmetric(vertical: space.m),
      padding: density.card,
      decoration: boxDecoration,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Dimension: mirrors the expand_less glyph's own reach so the
              // headline stays optically centred between them.
              if (widget.isRegenerate) const SizedBox(width: 24),
              Expanded(
                // M11b: the 🔄/✅ became a real glyph, centred WITH the text
                // as one unit rather than prefixed into the string. The outer
                // Row's 24px mirror is untouched, so the optical centring the
                // M6b comment describes still holds. `Flexible` around the
                // Text is deliberate: the Georgian headline may wrap, and a
                // bare Text beside an Icon in a Row would overflow at 1.3.
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      widget.isRegenerate ? Icons.autorenew : Icons.task_alt,
                      size: 20,
                      color: colors.ink,
                    ),
                    SizedBox(width: space.s),
                    Flexible(
                      child: Text(
                        widget.isRegenerate
                            ? 'განახლებული ინფორმაცია ხელმისაწვდომია'
                            : 'დამხმარემ საკმარისი ინფორმაცია შეაგროვა',
                        style: type.titleS.copyWith(color: colors.ink),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
              if (widget.isRegenerate)
                // 44×44 of reach around a 20px glyph WITHOUT making the header
                // row 44px tall (M6b §D).
                FuzzzyHitTarget(
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => setState(() => _expanded = false),
                    child: Icon(Icons.expand_less, size: 20, color: colors.ink),
                  ),
                ),
            ],
          ),
          SizedBox(height: space.m),
          SizedBox(
            width: double.infinity,
            // Dimension: the full-width CTA height, the same 48 M8 gave the
            // add-fact CTA. Replaces the fork's vertical padding, which was
            // the wrong axis for a button whose width is already forced.
            height: 48,
            child: ElevatedButton.icon(
              onPressed: widget.isBuilding ? null : widget.onBuild,
              // M11b: the label's 🔄/📁 folded INTO the button's existing icon
              // slot, which now switches with the state instead of showing
              // `auto_awesome` beside a second, contradicting emoji.
              icon: Icon(
                widget.isRegenerate ? Icons.autorenew : Icons.auto_awesome,
                size: 18,
              ),
              label: Text(
                widget.isRegenerate
                    ? 'საქმის ხელახლა გენერაცია'
                    : 'საქმის ანალიზის გენერაცია',
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.actionPrimaryBg,
                foregroundColor: colors.actionPrimaryFg,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
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
  const _MessageBubble({required this.message});
  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        margin: EdgeInsets.only(bottom: space.m),
        padding: density.snug,
        // `FuzzzyChatBubble`'s exact recipe (domain/fuzzzy_chat_bubble.dart:
        // 68-77), identical to `consultation_page._buildMessageBubble`:
        // sent = the actionPrimary pair with NO border, received = `surface`
        // plus a `line` hairline, and the tail corner is `radius.s` on the
        // sender's side with `radius.l` everywhere else. The fork's
        // gold-tint-vs-grey-panel pair becomes inverted mono, a stronger
        // distinction than the 0.15 alpha it replaces.
        //
        // The error bubble is the third rung: the sanctioned 0.12 lerp against
        // `ground` (never alpha — USING §2.4) inside `destructiveLine`. NOT
        // `errorBorder`, which is a form field's error border and nothing else
        // (MAPPING §2.6 corrects MIGRATION_RECIPE §2.1 here).
        decoration: BoxDecoration(
          color: isUser
              ? colors.actionPrimaryBg
              : message.isError
              ? Color.lerp(colors.ground, colors.destructive, 0.12)
              : colors.surface,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(radius.l),
            topRight: Radius.circular(radius.l),
            bottomLeft: Radius.circular(isUser ? radius.l : radius.s),
            bottomRight: Radius.circular(isUser ? radius.s : radius.l),
          ),
          border: isUser
              ? null
              : Border.all(
                  color: message.isError ? colors.destructiveLine : colors.line,
                ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser && message.trustLevel != null) ...[
              _TrustBadge(level: message.trustLevel!),
              SizedBox(height: space.s),
            ],
            SelectableText(
              message.isError && message.failureType != null
                  ? _failureMessageKa(message.failureType)
                  : message.displayText,
              // `height: 1.5` deleted — line-height belongs to the type role
              // (M6b). Sent text takes the inverted `actionPrimaryFg`.
              style: type.body.copyWith(
                color: message.isError
                    ? colors.destructiveText
                    : isUser
                    ? colors.actionPrimaryFg
                    : colors.ink,
              ),
            ),
            if (message.citations != null && message.citations!.isNotEmpty) ...[
              SizedBox(height: space.m),
              ...message.citations!.map(
                (c) {
                  final hasUrl = c.url != null && c.url!.isNotEmpty;
                  final content = Container(
                    margin: EdgeInsets.only(bottom: space.xs),
                    padding: density.chip,
                    // Parent-aware surface rule: this chip sits INSIDE a
                    // `surface` bubble, so its recessed rung is `ground`, not
                    // another `surface`. The fork's gold gavel + gold label
                    // go monochrome; the tappability is carried by the
                    // underline, which survives. M11 swaps this whole chip for
                    // `FuzzzyCitationChip`.
                    decoration: BoxDecoration(
                      color: colors.ground,
                      borderRadius: BorderRadius.circular(radius.s),
                      border: Border.all(color: colors.line),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.gavel, size: 12, color: colors.ink),
                        SizedBox(width: space.xs),
                        Expanded(
                          child: Text(
                            c.articleTitle,
                            style: type.bodyS.copyWith(
                              color: colors.ink,
                              decoration: hasUrl
                                  ? TextDecoration.underline
                                  : null,
                              // Without this the rule is drawn in the
                              // INHERITED colour, which after the role swap is
                              // not always the text's (M8 judgement 1).
                              decorationColor: hasUrl ? colors.ink : null,
                            ),
                          ),
                        ),
                        if (hasUrl) ...[
                          SizedBox(width: space.xs),
                          Icon(
                            Icons.open_in_new,
                            size: 12,
                            color: colors.inkMute,
                          ),
                        ],
                      ],
                    ),
                  );

                  if (hasUrl) {
                    return GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: () async {
                        final uri = Uri.parse(c.url!);
                        if (await canLaunchUrl(uri)) {
                          await launchUrl(uri);
                        }
                      },
                      child: MouseRegion(
                        cursor: SystemMouseCursors.click,
                        child: content,
                      ),
                    );
                  }
                  return content;
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// The AI answer's trust marker — `FuzzzyStatusChip`'s recipe, app-side.
///
/// `FuzzzyStatusChip` itself could NOT be used verbatim: its label takes
/// `fuzzzyTextStyles.label`, the uppercase mono eyebrow role, and these three
/// labels are Georgian — a family with no Georgian block and tracking that is
/// wrong for Mkhedruli (MAPPING §3 judgement 3). So this is the kit's own
/// recipe rebuilt on the roles with a Georgian-capable type role
/// (`fuzzzy_status_chip.dart:80-98`): NO fill, a 1px
/// `Color.lerp(ground, role, 0.40)` border, `density.chip`, `radius.s`, an 8px
/// leading disc in the role, and the label in the role's own colour.
///
/// The three levels map exactly as `harvest/mol.md` §1 specifies:
/// verified → `success` · interpretation → `warning` · general → `inkMute`
/// (`FuzzzyStatusKind.neutral`). That is also what MoL's own never-called
/// `verifiedColor` / `interpretationColor` / `guidanceColor` fields meant.
class _TrustBadge extends StatelessWidget {
  const _TrustBadge({required this.level});
  final String level;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final role = switch (level) {
      'verified' => colors.success,
      'interpretation' => colors.warning,
      _ => colors.inkMute,
    };
    // `neutral` draws a plain grey outline decoupled from its dot; every other
    // kind colour-mixes its own role into the border. Kit behaviour, copied.
    final border = level == 'verified' || level == 'interpretation'
        ? Color.lerp(colors.ground, role, 0.40)!
        : Color.lerp(colors.ground, colors.lineStrong, 0.40)!;

    return Container(
      padding: density.chip,
      decoration: BoxDecoration(
        border: Border.all(color: border),
        borderRadius: BorderRadius.circular(radius.s),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            // Dimension: §4.4's ONE sanctioned status-dot diameter. It
            // replaces the ✓ / ◐ / ○ glyphs the fork prefixed to each label —
            // the dot IS what those stood for, and M7/M8 already reduced this
            // app's other taxonomies to the same disc.
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: role,
              borderRadius: BorderRadius.circular(radius.circle),
            ),
          ),
          SizedBox(width: space.s),
          Text(
            _trustLabel(level),
            // caption11 + w600 → `control`, the w600 role (M6 rule). The
            // explicit `fontWeight: w600` the fork bolted on is deleted: weight
            // belongs to the type role.
            style: type.control.copyWith(color: role),
          ),
        ],
      ),
    );
  }

  static String _trustLabel(String level) => switch (level) {
    'verified' => 'დადასტურებული',
    'interpretation' => 'ინტერპრეტაცია',
    _ => 'ზოგადი მითითება',
  };
}

/// Typing indicator shown while AI is responding.
class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.only(bottom: space.m),
        padding: density.snug,
        decoration: BoxDecoration(
          // Same box as a received bubble — it IS one, still filling. It also
          // GAINS the `line` hairline the fork never drew, so it does not
          // float unbounded on `ground`.
          color: colors.surface,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(radius.l),
            topRight: Radius.circular(radius.l),
            bottomRight: Radius.circular(radius.l),
            bottomLeft: Radius.circular(radius.s),
          ),
          border: Border.all(color: colors.line),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              // Dimension: the inline spinner's own footprint.
              width: 16,
              height: 16,
              child: _Spinner(),
            ),
            SizedBox(width: space.s),
            Text(
              'დამხმარე ფიქრობს...',
              style: type.body.copyWith(color: colors.inkMute),
            ),
          ],
        ),
      ),
    );
  }
}

String _failureMessageKa(ConsultationFailureType? type) => switch (type) {
  ConsultationFailureType.network =>
    'სერვერთან დაკავშირება ვერ მოხერხდა.\nშეამოწმეთ ინტერნეტ კავშირი.',
  ConsultationFailureType.unauthorized =>
    'სესია ვადაგასულია.\nგთხოვთ ხელახლა შეხვიდეთ.',
  ConsultationFailureType.noCredits =>
    'კრედიტები ამოიწურა.\nშეიძინეთ დამატებითი.',
  ConsultationFailureType.rateLimited =>
    'მოთხოვნების ლიმიტი ამოიწურა.\nსცადეთ ცოტა მოგვიანებით.',
  ConsultationFailureType.notFound => 'მოთხოვნილი რესურსი ვერ მოიძებნა.',
  ConsultationFailureType.serverError =>
    'სერვერის შეცდომა.\nგთხოვთ ცოტა მოგვიანებით სცადოთ.',
  ConsultationFailureType.unknown ||
  null => 'უცნობი შეცდომა მოხდა.\nხელახლა სცადეთ.',
};

class _PendingConfirmationCard extends StatelessWidget {
  const _PendingConfirmationCard({
    required this.data,
    required this.onConfirm,
    required this.onReject,
  });

  final ToolResultData data;
  final VoidCallback onConfirm;
  final VoidCallback onReject;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Container(
      margin: EdgeInsets.only(bottom: space.s),
      padding: density.tile,
      // This card is the gate in front of a mutating tool call (delete_fact,
      // delete_risk, …), so `destructive` is the honest voice and the fork's
      // `errorColor` maps straight through (MAPPING §2.6). Alpha 0.1 → the
      // sanctioned 0.12 lerp against `ground`; the 0.3 border → `destructiveLine`.
      decoration: BoxDecoration(
        color: Color.lerp(colors.ground, colors.destructive, 0.12),
        borderRadius: BorderRadius.circular(radius.m),
        border: Border.all(color: colors.destructiveLine),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.warning_amber_rounded,
                size: 20,
                color: colors.destructiveText,
              ),
              SizedBox(width: space.s),
              Expanded(
                child: Text(
                  'დასადასტურებელი მოქმედება: ${_toolNameKa(data.toolName)}',
                  style: type.control.copyWith(color: colors.destructiveText),
                ),
              ),
            ],
          ),
          if (data.description != null && data.description!.isNotEmpty) ...[
            SizedBox(height: space.s),
            Text(
              data.description!,
              style: type.body.copyWith(color: colors.ink),
            ),
          ],
          SizedBox(height: space.m),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: onReject,
                // A button label is the `control` role, not `titleS`: the fork
                // used `bodyBold14` because it had no button-label style.
                child: Text(
                  'გაუქმება',
                  style: type.control.copyWith(color: colors.inkMute),
                ),
              ),
              SizedBox(width: space.s),
              ElevatedButton(
                onPressed: onConfirm,
                // The one sanctioned destructive FILL on this screen (USING §6
                // duty 4 — a commit). `onRed` is the foreground that belongs on
                // it; the fork used the page colour, which only happened to be
                // legible.
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.destructive,
                  foregroundColor: colors.onRed,
                  padding: density.tile,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                ),
                child: const Text('დადასტურება'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

String _toolNameKa(String name) => switch (name) {
  'add_fact' => 'ფაქტის დამატება',
  'edit_fact' => 'ფაქტის რედაქტირება',
  'delete_fact' => 'ფაქტის წაშლა',
  'add_argument' => 'არგუმენტის დამატება',
  'delete_argument' => 'არგუმენტის წაშლა',
  'link_article' => 'მუხლის მიბმა',
  'unlink_article' => 'მუხლის მოხსნა',
  'set_strategy' => 'სტრატეგიის დაყენება',
  'add_action_item' => 'დავალების დამატება',
  'add_risk' => 'რისკის დამატება',
  'delete_risk' => 'რისკის წაშლა',
  _ => name,
};
