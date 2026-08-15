import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

class ConsultationPage extends StatefulWidget {
  const ConsultationPage({super.key});

  @override
  State<ConsultationPage> createState() => _ConsultationPageState();
}

class _ConsultationPageState extends State<ConsultationPage>
    with TickerProviderStateMixin {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  bool _actionChipsDismissed = false;
  bool _showScrollToBottom = false;
  late final AnimationController _dotAnimController;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    // Duration is a MOTION ROLE, and roles need a BuildContext — so the
    // controller is created bare here and given `motion.pulse` (plus its first
    // `repeat()`) in didChangeDependencies. Constructing it with a literal
    // duration would hardcode the one number the brand pack owns.
    _dotAnimController = AnimationController(vsync: this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // The typing dots are a looping ambient beat, not a transition:
    // `motion.pulse` is the role for exactly that (1600ms in Ink).
    final pulse = context.fuzzzyMotion.pulse;
    if (_dotAnimController.duration != pulse) {
      _dotAnimController
        ..duration = pulse
        ..repeat();
    }
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _messageController.dispose();
    _scrollController.dispose();
    _dotAnimController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final shouldShow = !_isNearBottom();
    if (shouldShow != _showScrollToBottom) {
      setState(() => _showScrollToBottom = shouldShow);
    }
  }

  bool _isNearBottom() {
    if (!_scrollController.hasClients) return true;
    final pos = _scrollController.position;
    // Consider "near bottom" if within 150px of the end (forward list scrolls to maxExtent)
    // For reversed list, bottom is position 0 — but we keep this for the reversed case too.
    return pos.pixels <= 150.0;
  }

  void _scrollToBottom({bool force = false}) {
    // Read the role now: the callback runs after the frame, when reading an
    // InheritedWidget off a possibly-unmounted State would be unsafe.
    final motion = context.fuzzzyMotion;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      if (force || _isNearBottom()) {
        _scrollController.animateTo(
          0,
          duration: motion.standard,
          curve: motion.standardCurve,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final motion = context.fuzzzyMotion;

    return Scaffold(
      appBar: AppBar(
        // Title style + leading/action icon colours come from appBarTheme
        // (titleM + ink), which M1 built from kit roles.
        title: const Text('AI კონსულტაცია'),
        leading: IconButton(
          icon: const Icon(Icons.history),
          onPressed: () => _showHistorySheet(context),
        ),
        actions: [
          BlocBuilder<ConsultationCubit, ConsultationState>(
            builder: (context, state) {
              if (state.status == StateStatus.initial) {
                return const SizedBox.shrink();
              }
              return IconButton(
                icon: const Icon(Icons.add_comment_outlined),
                tooltip: 'ახალი საუბარი',
                onPressed: () => context.read<ConsultationCubit>().reset(),
              );
            },
          ),
          BlocBuilder<ConsultationCubit, ConsultationState>(
            builder: (context, state) {
              //TODO enable sooner if needed
              if (state.status == StateStatus.initial ||
                  state.messages.length < 6) {
                return const SizedBox.shrink();
              }
              return IconButton(
                icon: const Icon(Icons.description_outlined),
                tooltip: 'საქმის გენერაცია',
                onPressed: state.isBuildingCase
                    ? null
                    : () => _triggerCaseBuild(context),
              );
            },
          ),
          BlocBuilder<ConsultationCubit, ConsultationState>(
            buildWhen: (prev, curr) => prev.chatMode != curr.chatMode,
            builder: (context, state) {
              final lawsOnly = state.chatMode == ChatMode.lawsOnly;
              return GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => _showModeSelector(context),
                child: Container(
                  margin: EdgeInsets.only(right: space.m),
                  padding: density.chip,
                  // CONSTANT appearance in both modes. The fork tinted this
                  // pill gold for `lawsOnly` and grey for `allSources`, which
                  // made one of two equal modes look "on". The mode is already
                  // carried by the icon and by `labelKa`; a hue on top of that
                  // is a second, redundant (and now monochrome) voice.
                  decoration: BoxDecoration(
                    color: colors.surface,
                    borderRadius: BorderRadius.circular(radius.m),
                    border: Border.all(color: colors.line),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        lawsOnly ? Icons.menu_book : Icons.auto_awesome,
                        size: 14,
                        color: colors.ink,
                      ),
                      SizedBox(width: space.xs),
                      Text(
                        state.chatMode.labelKa,
                        // `control` IS the w600 role — the fork's caption11 +
                        // fontWeight override becomes a role choice.
                        style: type.control.copyWith(color: colors.ink),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: BlocConsumer<ConsultationCubit, ConsultationState>(
        listenWhen: (prev, curr) {
          if (prev.messages.length != curr.messages.length) return true;
          if (prev.streamingStatus != curr.streamingStatus) return true;
          // A stage change repaints the indicator and nothing else, but it is
          // the ONLY thing moving for most of a 30-120s answer — drop it and
          // the progress rail freezes on its first value.
          if (prev.stage != curr.stage) return true;
          if (curr.streamingMessageId != null && curr.messages.isNotEmpty) {
            final prevMsg = prev.messages
                .where((m) => m.id == curr.streamingMessageId)
                .firstOrNull;
            final currMsg = curr.messages
                .where((m) => m.id == curr.streamingMessageId)
                .firstOrNull;
            if (prevMsg != null &&
                currMsg != null &&
                prevMsg.text.length != currMsg.text.length) {
              return true;
            }
          }
          return false;
        },
        listener: (context, state) => _scrollToBottom(),
        builder: (context, state) {
          if (state.status == StateStatus.initial) {
            return _buildWelcome(context, state);
          }
          if (state.status == StateStatus.loading && state.messages.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.status == StateStatus.failed && state.messages.isEmpty) {
            return _buildFailedState(context, state);
          }
          return Stack(
            children: [
              Column(
                children: [
                  Expanded(child: _buildMessageList(context, state)),
                  if (state.isAgentMode) _buildAgentModeBanner(context, state),
                  if (state.caseAnalysisReady &&
                      !state.hasCaseAttached &&
                      !state.isAgentMode)
                    _buildCaseReadyBanner(context, state),
                  if (state.hasCaseAttached)
                    _buildAttachedCaseBanner(context, state),
                  _buildInputBar(context, state),
                ],
              ),
              // Scroll-to-bottom floating button
              if (_showScrollToBottom)
                Positioned(
                  // Dimension: clears the docked composer so the button never
                  // sits on top of the send affordance.
                  bottom: 90 + MediaQuery.of(context).padding.bottom,
                  right: space.l,
                  child: AnimatedOpacity(
                    opacity: _showScrollToBottom ? 1.0 : 0.0,
                    duration: motion.standard,
                    curve: motion.standardCurve,
                    // The kit's sanctioned way to reach 44×44 without moving a
                    // painted pixel (shared/fuzzzy_hit_target.dart, RUN_DECISIONS
                    // decision 3) — a ConstrainedBox would reflow the host.
                    child: FuzzzyHitTarget(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: () => _scrollToBottom(force: true),
                        child: Container(
                          // Dimension: the button's own footprint.
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: colors.surface,
                            // Ink's elevation step is the BORDER — the fork's
                            // BoxShadow is deleted, not translated.
                            borderRadius: BorderRadius.circular(radius.circle),
                            border: Border.all(color: colors.line),
                          ),
                          child: Icon(
                            Icons.keyboard_arrow_down,
                            color: colors.ink,
                            size: 22,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              if (state.isBuildingCase)
                ColoredBox(
                  // A blocking veil over the page. The kit's own precedent for
                  // this is `ground` at high alpha (fuzzzy_dropzone.dart:66) —
                  // never Colors.black, which is a light-skin bug waiting.
                  color: colors.ground.withValues(alpha: 0.82),
                  child: Center(
                    child: Container(
                      padding: density.dialog,
                      decoration: BoxDecoration(
                        // Overlay rung (USING §3): `raised` + `lineStrong`.
                        color: colors.raised,
                        borderRadius: BorderRadius.circular(radius.l),
                        border: Border.all(color: colors.lineStrong),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const CircularProgressIndicator(),
                          SizedBox(height: space.l),
                          Text(
                            'საქმე მზადდება...',
                            style: type.titleS.copyWith(color: colors.ink),
                          ),
                          SizedBox(height: space.s),
                          Text(
                            'ეს შეიძლება 30-60 წამი გაგრძელდეს',
                            style: type.bodyS.copyWith(color: colors.inkMute),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildWelcome(BuildContext context, ConsultationState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return // 🔴 M14b. A centred state panel is NOT free of layout risk: this one
    // overflowed the viewport by up to 268 px on the BOTTOM under the
    // stress pack (`case_chat_section.dart:300` fired at 1.0 AND 1.3) — a
    // 64 px glyph, two texts and a button simply do not fit once the pack
    // inflates type and spacing, and a `Center` has nothing to give.
    //
    // Scroll it, but keep it centred while it still fits: the
    // `ConstrainedBox(minHeight: viewport)` preserves the existing look
    // exactly — without it the panel jumps to the top of every screen it
    // appears on. Same class as T-0257 (feedback_sheet), one screen over.
    LayoutBuilder(
      builder: (context, viewport) => SingleChildScrollView(
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: viewport.maxHeight),
          child: Center(
            child: Padding(
              // A centred state panel's inset is a component FOOTPRINT, so it takes
              // a density tier, not `space.xxl` (USING §4.3) — even though 32 → 32
              // would have matched by number.
              padding: density.screen,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Oversized decorative state glyph → `inkFaint`, alpha deleted.
                  Icon(Icons.psychology, size: 64, color: colors.inkFaint),
                  SizedBox(height: space.xl),
                  Text(
                    'AI კონსულტაცია',
                    style: type.titleM.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.s),
                  Text(
                    'დაუსვით იურიდიული კითხვა',
                    style: type.body.copyWith(color: colors.inkMute),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(height: space.xl),
                  // 🔴 M14b: this row overflowed 96 px on the RIGHT under the
                  // stress pack. Two mode buttons with Georgian labels side by
                  // side, and the row constrained neither. `Wrap`, not
                  // `Flexible`: these are TAP TARGETS, so shrinking or
                  // ellipsing them would trade an overflow for a sub-44×44
                  // target and an unreadable affordance — both defects in
                  // their own right (plan §4). Dropping the second button onto
                  // its own line costs nothing now that the panel scrolls.
                  Wrap(
                    alignment: WrapAlignment.center,
                    spacing: space.m,
                    runSpacing: space.s,
                    children: [
                      _buildModeButton(
                        context,
                        ChatMode.lawsOnly,
                        state.chatMode,
                      ),
                      _buildModeButton(
                        context,
                        ChatMode.allSources,
                        state.chatMode,
                      ),
                    ],
                  ),
                  SizedBox(height: space.xxl),
                  // `FuzzzyButton.primary`: actionPrimary pair, radius.m, `snug`.
                  ElevatedButton.icon(
                    onPressed: () =>
                        context.read<ConsultationCubit>().startConversation(),
                    icon: const Icon(Icons.chat),
                    label: const Text('დაწყება'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colors.actionPrimaryBg,
                      foregroundColor: colors.actionPrimaryFg,
                      padding: density.snug,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(radius.m),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFailedState(BuildContext context, ConsultationState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return Center(
      child: Padding(
        padding: density.screen,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // The oversized glyph is decoration, not the error VOICE — the
            // copy under it carries that. Red on a 64px icon would be the
            // screen's loudest element (USING §6, one red voice).
            Icon(Icons.cloud_off, size: 64, color: colors.inkFaint),
            SizedBox(height: space.xl),
            Text(
              'კავშირი ვერ მოხერხდა',
              style: type.titleM.copyWith(color: colors.ink),
            ),
            SizedBox(height: space.s),
            Text(
              _errorMessageKa(state.failureType),
              style: type.body.copyWith(color: colors.inkMute),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xl),
            ElevatedButton.icon(
              onPressed: () =>
                  context.read<ConsultationCubit>().startConversation(),
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('ხელახლა ცდა'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.actionPrimaryBg,
                foregroundColor: colors.actionPrimaryFg,
                padding: density.snug,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModeButton(
    BuildContext context,
    ChatMode mode,
    ChatMode currentMode,
  ) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final isSelected = mode == currentMode;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () => context.read<ConsultationCubit>().switchMode(mode),
      child: Container(
        padding: density.snug,
        decoration: BoxDecoration(
          // Discrete choice → INVERTED-MONO fill from the action pair
          // (USING §6: never red, never a tint ladder). Border width is
          // CONSTANT and only its colour changes, so selecting never reflows
          // the row — the fork also swapped fontWeight w400→w600, which
          // re-measured the label. Both are gone.
          color: isSelected ? colors.actionPrimaryBg : colors.surface,
          borderRadius: BorderRadius.circular(radius.m),
          border: Border.all(
            color: isSelected ? colors.actionPrimaryBg : colors.line,
          ),
        ),
        child: Column(
          children: [
            Icon(
              mode == ChatMode.lawsOnly ? Icons.menu_book : Icons.auto_awesome,
              color: isSelected ? colors.actionPrimaryFg : colors.inkMute,
            ),
            SizedBox(height: space.xs),
            Text(
              mode.labelKa,
              style: type.control.copyWith(
                color: isSelected ? colors.actionPrimaryFg : colors.inkMute,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList(BuildContext context, ConsultationState state) {
    final space = context.fuzzzySpace;

    // Show action chips after first AI response (2 messages: user + AI)
    final showChips =
        !_actionChipsDismissed &&
        state.messages.length >= 2 &&
        !state.isSending &&
        state.messages.last.isUser == false;

    // We only show the typing indicator if we're sending and haven't received any text yet
    final streamingMsg = state.streamingMessageId != null
        ? state.messages
              .where((m) => m.id == state.streamingMessageId)
              .firstOrNull
        : null;
    final showTypingIndicator =
        state.isSending && (streamingMsg == null || streamingMsg.text.isEmpty);

    // Filter out the empty streaming message if we're showing the typing indicator instead
    final displayMessages = state.messages
        .where((m) => !(m.id == state.streamingMessageId && m.text.isEmpty))
        .toList();

    return ListView.builder(
      controller: _scrollController,
      reverse: true,
      physics: const BouncingScrollPhysics(),
      padding: EdgeInsets.symmetric(horizontal: space.m, vertical: space.l),
      // Item order (reversed list): index 0 = visually at bottom
      //   [0]           typing indicator (if active)
      //   [1..N]        messages newest-first
      //   [N+1]         action chips (if visible)
      itemCount:
          displayMessages.length +
          (showTypingIndicator ? 1 : 0) +
          (showChips ? 1 : 0),
      itemBuilder: (context, index) {
        // Typing indicator at the very bottom (index 0 in reversed list)
        if (showTypingIndicator && index == 0) {
          return _buildTypingIndicator(context, state);
        }
        // Offset index by 1 when the typing indicator occupies slot 0
        final offset = showTypingIndicator ? 1 : 0;
        final msgSlot = index - offset;
        if (msgSlot < displayMessages.length) {
          // Reverse: show newest message first (at bottom)
          final reversedIndex = displayMessages.length - 1 - msgSlot;
          return _buildMessageBubble(context, displayMessages[reversedIndex]);
        }
        if (showChips) {
          return _buildActionChips(context);
        }
        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildActionChips(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Container(
      margin: EdgeInsets.symmetric(vertical: space.s),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'როგორ გსურთ გაგრძელება?',
            style: type.control.copyWith(color: colors.inkMute),
          ),
          SizedBox(height: space.s),
          Wrap(
            spacing: space.s,
            runSpacing: space.s,
            children: [
              // The three suggestions are peers — the fork gave them three
              // different hues (gold / green / grey), which read as three
              // different KINDS of action. They are one kind, so they are one
              // appearance; the icon and the label carry the difference.
              _ActionChip(
                icon: Icons.quiz_outlined,
                label: 'დამაზუსტე',
                onTap: () {
                  setState(() => _actionChipsDismissed = true);
                  context.read<ConsultationCubit>().sendMessage(
                    'გთხოვ, დამისვი დამაზუსტებელი კითხვები ჩემი სიტუაციის შესახებ, რომ უკეთესად გამიგო და დამეხმარო.',
                  );
                },
              ),
              _ActionChip(
                icon: Icons.auto_awesome,
                label: 'სრული ანალიზი',
                onTap: () {
                  setState(() => _actionChipsDismissed = true);
                  context.read<ConsultationCubit>().sendMessage(
                    'გთხოვ, გამიკეთე ჩემი სიტუაციის სრული იურიდიული ანალიზი — ყველა შესაბამისი კანონის მუხლით, სტრატეგიით და რეკომენდაციებით.',
                  );
                },
              ),
              _ActionChip(
                icon: Icons.chat_bubble_outline,
                label: 'გავაგრძელო',
                onTap: () {
                  setState(() => _actionChipsDismissed = true);
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(BuildContext context, ChatMessage message) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    if (message.isError) {
      return Container(
        margin: EdgeInsets.only(bottom: space.m),
        padding: density.tile,
        decoration: BoxDecoration(
          // A tinted panel is Color.lerp against `ground`, never alpha
          // (USING §2.4). Error bubbles are the sanctioned 0.12 rung.
          color: Color.lerp(colors.ground, colors.destructive, 0.12),
          borderRadius: BorderRadius.circular(radius.m),
          // NOT `errorBorder` — that role is a form field's error border and
          // nothing else. A chat error bubble takes `destructiveLine`
          // (MAPPING §2.6 corrects MIGRATION_RECIPE §2.1 here).
          border: Border.all(color: colors.destructiveLine),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline, color: colors.destructiveText, size: 18),
            SizedBox(width: space.s),
            Expanded(
              child: Text(
                _errorMessageKa(message.failureType),
                style: type.body.copyWith(color: colors.destructiveText),
              ),
            ),
          ],
        ),
      );
    }

    final screenWidth = MediaQuery.of(context).size.width;
    final maxBubbleWidth = message.isUser
        ? screenWidth * 0.82
        : screenWidth * 0.92;

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: () {
          Clipboard.setData(ClipboardData(text: message.text));
          FuzzzyToast.show(
            context,
            message: 'გადაკოპირებულია',
            kind: FuzzzyToastKind.success,
            qaId: 'consultation.copied',
          );
        },
        child: Container(
          margin: EdgeInsets.only(bottom: space.s),
          constraints: BoxConstraints(maxWidth: maxBubbleWidth),
          padding: density.tile,
          // FuzzzyChatBubble's exact recipe (domain/fuzzzy_chat_bubble.dart:
          // 68-77): sent = actionPrimary pair with NO border, received =
          // `surface` + a `line` hairline; the tail corner is radius.s on the
          // sender's side and radius.l everywhere else. The fork's gold-tint
          // vs grey-panel pair becomes inverted-mono, which is a stronger
          // distinction than the 0.12 tint it replaces.
          decoration: BoxDecoration(
            color: message.isUser ? colors.actionPrimaryBg : colors.surface,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(radius.l),
              topRight: Radius.circular(radius.l),
              bottomLeft: Radius.circular(message.isUser ? radius.l : radius.s),
              bottomRight: Radius.circular(
                message.isUser ? radius.s : radius.l,
              ),
            ),
            border: message.isUser ? null : Border.all(color: colors.line),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(
                message.displayText,
                // `height: 1.6` deleted — line-height belongs to the type role.
                style: type.body.copyWith(
                  color: message.isUser ? colors.actionPrimaryFg : colors.ink,
                ),
              ),
              if (message.toolResults != null &&
                  message.toolResults!.isNotEmpty) ...[
                SizedBox(height: space.s),
                ...message.toolResults!.map(
                  (t) => _buildToolResultChip(context, t),
                ),
              ],
              if (message.citations != null &&
                  message.citations!.isNotEmpty) ...[
                SizedBox(height: space.m),
                // Colour and thickness come from dividerTheme (line, 1px).
                const Divider(),
                SizedBox(height: space.s),
                ...message.citations!.map(
                  (c) => _buildCitationChip(context, c),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCitationChip(BuildContext context, CitationData citation) {
    // M11d: one of four identical hand-rolled citation chips, now
    // `AppCitationChip`. This one is the only one that navigates IN-app, so it
    // takes no `open_in_new` trailing glyph. It sits on the message column's
    // `ground`, hence `AppChipParent.ground` → a `surface` box.
    return Padding(
      padding: EdgeInsets.only(bottom: context.fuzzzySpace.xs),
      child: AppCitationChip(
        label: citation.articleTitle.isNotEmpty
            ? citation.articleTitle
            : 'მუხლი ${citation.articleId}',
        parent: AppChipParent.ground,
        leading: const Icon(Icons.article_outlined),
        onTap: () => _navigateToArticle(context, citation),
        qaId: citation.articleId,
      ),
    );
  }

  Widget _buildToolResultChip(BuildContext context, ToolResultData tool) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    // The switch used to also carry a Color per tool (green / purple / grey).
    // Three literal hues for three flavours of "a tool ran" is decoration, not
    // meaning — the icon already names the tool. Colour dropped from the tuple.
    // M11b: the 📁/✨/✅ prefixes are DROPPED, not re-iconified — this chip
    // already renders `icon` to the left of `label`, so the emoji was a second
    // glyph competing with the Material one three pixels away.
    final (IconData icon, String label) = switch (tool.toolName) {
      'create_case' => (
        Icons.create_new_folder_outlined,
        '${_toolNameKaStatic(tool.toolName)}: ${tool.result['title'] ?? ''}',
      ),
      'build_case_analysis' => (
        Icons.auto_awesome,
        _toolNameKaStatic(tool.toolName),
      ),
      _ => (Icons.build_circle_outlined, _toolNameKaStatic(tool.toolName)),
    };

    return Container(
      margin: EdgeInsets.only(bottom: space.xs),
      padding: density.chip,
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.s),
        border: Border.all(color: colors.line),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: colors.inkMute),
          SizedBox(width: space.xs),
          Flexible(
            child: Text(
              label,
              // caption11 + w600 → `control`, the w600 role (M6 rule).
              style: type.control.copyWith(color: colors.ink),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  static String _toolNameKaStatic(String name) => switch (name) {
    'add_fact' => 'ფაქტი დამატებულია',
    'edit_fact' => 'ფაქტი განახლდა',
    'delete_fact' => 'ფაქტი წაშლილია',
    'add_argument' => 'არგუმენტი დამატებულია',
    'delete_argument' => 'არგუმენტი წაშლილია',
    'link_article' => 'მუხლი მიბმულია',
    'set_strategy' => 'სტრატეგია დაყენებულია',
    'add_action_item' => 'დავალება დამატებულია',
    'add_risk' => 'რისკი დამატებულია',
    'get_case_summary' => 'საქმის მიმოხილვა',
    'create_case' => 'საქმე შეიქმნა',
    'build_case_analysis' => 'სრული ანალიზი',
    _ => name,
  };

  void _navigateToArticle(BuildContext context, CitationData citation) {
    final url = citation.url;
    // If we have a real matsne.gov.ge URL, open it externally
    if (url != null && url.isNotEmpty && url.contains('matsne.gov.ge')) {
      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      return;
    }
    // Fallback: internal article page
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => BlocProvider(
          create: (_) => LawsCubit(
            repository: LawsRepository(
              remoteDataSource: LawsRemoteDataSource(),
            ),
          )..loadArticle(citation.articleId),
          child: LawArticlePage(
            articleId: citation.articleId,
            articleTitle: citation.articleTitle.isNotEmpty
                ? citation.articleTitle
                : 'მუხლი ${citation.articleId}',
            codeName: citation.codeTitle,
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator(BuildContext context, ConsultationState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final motion = context.fuzzzyMotion;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.only(bottom: space.s),
        padding: density.snug,
        decoration: BoxDecoration(
          // Same box as a received bubble — it IS one, still filling.
          color: colors.surface,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(radius.l),
            topRight: Radius.circular(radius.l),
            bottomLeft: Radius.circular(radius.s),
            bottomRight: Radius.circular(radius.l),
          ),
          border: Border.all(color: colors.line),
        ),
        // Sized to the conversation column, not to the text: a long Georgian
        // stage name at a large text scale must wrap inside the bubble rather
        // than push it past the gutter (the M14b overflow class).
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.78,
        ),
        child: () {
          final stage = state.stage;
          final label = stage?.label ?? state.streamingStatus;
          final row = Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: List.generate(
                  3,
                  (i) => AnimatedBuilder(
                    animation: _dotAnimController,
                    builder: (_, child) {
                      final delay = i * 0.2;
                      final t = (_dotAnimController.value - delay).clamp(
                        0.0,
                        1.0,
                      );
                      final bounce = (t < 0.5) ? (t * 2) : (2 - t * 2);
                      return Transform.translate(
                        offset: Offset(0, -3 * bounce),
                        child: child,
                      );
                    },
                    child: Container(
                      // Dimensions: the dot's own footprint and its optical
                      // half-gap. Not a `space` rung — 7px dots on a 4px ramp
                      // would round to a different animation.
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                      width: 7,
                      height: 7,
                      decoration: BoxDecoration(
                        // Alpha 0.5 deleted: `inkMute` IS the de-emphasised rung.
                        color: colors.inkMute,
                        borderRadius: BorderRadius.circular(radius.circle),
                      ),
                    ),
                  ),
                ),
              ),
              if (label != null) ...[
                SizedBox(width: space.m),
                Flexible(
                  child: Text(
                    label,
                    // `fontStyle: italic` deleted — Ink has no italic face, so
                    // it would be a synthesised oblique. Unlike M6's "skipped"
                    // placeholder this is LIVE information the user reads, so it
                    // keeps `inkMute` rather than dropping to `inkFaint`.
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                ),
              ],
            ],
          );

          if (stage == null) return row;

          // With a real stage we can show POSITION, not just motion. Answers
          // take 30-120s; "…" for two minutes reads as a hang, whereas a named
          // stage that advances reads as work. The detail line is deliberately
          // concrete ("23 articles found") — a number is evidence the step did
          // something, which reassurance cannot be.
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              row,
              if (stage.detail != null) ...[
                SizedBox(height: space.xs),
                Text(
                  stage.detail!,
                  // One rung quieter than the stage name: it qualifies the
                  // stage, it does not compete with it.
                  style: type.bodyS.copyWith(color: colors.inkFaint),
                ),
              ],
              SizedBox(height: space.s),
              ClipRRect(
                borderRadius: BorderRadius.circular(radius.l),
                child: TweenAnimationBuilder<double>(
                  // Stages fire in uneven jumps (a request skips whatever it
                  // does not need), so the rail is TWEENED — an instant jump
                  // from 0.2 to 0.7 reads as a glitch, a 300ms slide reads as
                  // progress.
                  tween: Tween(begin: 0, end: stage.progress),
                  // Pack-bound, not a literal: the guard is right that a
                  // hardcoded duration is a pixel the brand pack can no
                  // longer control. `standard` is the rung for a state
                  // change the user is watching, which is what this is.
                  duration: motion.standard,
                  curve: motion.standardCurve,
                  builder: (context, value, _) => LinearProgressIndicator(
                    value: value,
                    // The empty rung of a progress bar IS `track` (MAPPING §2.3).
                    backgroundColor: colors.track,
                    valueColor: AlwaysStoppedAnimation(colors.ink),
                    // Dimension: the bar's 4px rail, matching the questionnaire.
                    minHeight: 4,
                  ),
                ),
              ),
            ],
          );
        }(),
      ),
    );
  }

  Widget _buildInputBar(BuildContext context, ConsultationState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final bottomPadding = MediaQuery.of(context).padding.bottom;
    return Container(
      // Docked bar idiom (M6): safe-area bottom + a `space` rung. The
      // horizontal inset stays at `space.s`, NOT `density.screen`, because the
      // two flanking IconButtons already carry Material's own 8px inset.
      padding: EdgeInsets.fromLTRB(
        space.s,
        space.m,
        space.s,
        bottomPadding + space.m,
      ),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(top: BorderSide(color: colors.line)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Case attachment button
          Padding(
            padding: EdgeInsets.only(bottom: space.xs),
            child: IconButton(
              icon: Icon(
                state.hasCaseAttached
                    ? Icons.folder
                    : Icons.folder_open_outlined,
                color: state.hasCaseAttached ? colors.ink : colors.inkMute,
                size: 22,
              ),
              onPressed: () => _showCaseSelector(context),
              tooltip: 'საქმის მიმაგრება',
              visualDensity: VisualDensity.compact,
            ),
          ),
          Expanded(
            child: ConstrainedBox(
              // Dimension: caps the composer at ~5 lines before it scrolls.
              constraints: const BoxConstraints(maxHeight: 120),
              child: TextField(
                controller: _messageController,
                style: type.body.copyWith(color: colors.fieldText),
                // The whole box — fill, all five border states, corner radius,
                // content padding and hint style — now comes from M1's
                // inputDecorationTheme, which is built from FuzzzyFormStyles.
                // The fork wrapped this field in a Container just to fake a
                // fill and a 22px radius; that wrapper is gone (RUN_BRIEF §4:
                // never re-declare field decoration locally).
                decoration: const InputDecoration(
                  hintText: 'დაწერეთ კითხვა...',
                ),
                maxLines: 5,
                minLines: 1,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _sendMessage(context, state),
              ),
            ),
          ),
          SizedBox(width: space.s),
          Padding(
            padding: EdgeInsets.only(bottom: space.xs),
            // `FuzzzyButton`'s disabled visual is Opacity(0.42) over the SAME
            // fill (buttons/fuzzzy_button.dart:174) — never a second, faded
            // colour pair. Geometry is identical in both states.
            child: Opacity(
              opacity: state.isSending ? 0.42 : 1.0,
              child: FuzzzyHitTarget(
                enabled: !state.isSending,
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: state.isSending
                      ? null
                      : () => _sendMessage(context, state),
                  child: Container(
                    // Dimension: the send affordance's own footprint. The 44×44
                    // touch minimum is met by FuzzzyHitTarget without growing it.
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: colors.actionPrimaryBg,
                      borderRadius: BorderRadius.circular(radius.circle),
                    ),
                    child: Icon(
                      Icons.arrow_upward_rounded,
                      color: colors.actionPrimaryFg,
                      size: 20,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAgentModeBanner(BuildContext context, ConsultationState state) {
    return _Banner(
      icon: Icons.folder_special,
      // Tools are wired and working — the affirmative rung of FuzzzyBanner.
      tint: _BannerTint.success,
      // M11b: the 📂 is DROPPED — `_Banner` already renders `icon`.
      message: 'საქმე დაკავშირებულია — AI ინსტრუმენტები აქტიურია',
      onDismiss: () => context.read<ConsultationCubit>().exitAgentMode(),
    );
  }

  Widget _buildAttachedCaseBanner(
    BuildContext context,
    ConsultationState state,
  ) {
    return _Banner(
      icon: Icons.folder,
      // A statement of WHAT is attached, not a success — `info`.
      tint: _BannerTint.info,
      message: state.attachedCaseTitle ?? 'საქმე',
      onDismiss: () => context.read<ConsultationCubit>().detachCase(),
    );
  }

  Widget _buildCaseReadyBanner(BuildContext context, ConsultationState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return Container(
      margin: EdgeInsets.symmetric(horizontal: space.l, vertical: space.s),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.m),
        border: Border.all(color: colors.line),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // FuzzzyBanner's 3px tinted left rule (containers/fuzzzy_banner.dart)
            // replaces the fork's full green tint + green border + green text.
            // IntrinsicHeight, not a fixed height: at textScaler 1.3 the Georgian
            // copy grows and a 48px rule would stop short of the box.
            Container(width: 3, color: colors.success),
            Expanded(
              child: Padding(
                padding: density.notice,
                child: Row(
                  children: [
                    Icon(
                      Icons.check_circle_outline,
                      color: colors.success,
                      size: 24,
                    ),
                    SizedBox(width: space.m),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'საკმარისი კონტექსტი შეგროვდა',
                            style: type.titleS.copyWith(color: colors.ink),
                          ),
                          SizedBox(height: space.xs),
                          Text(
                            'AI მზადაა საქმის დასაგენერირებლად',
                            style: type.bodyS.copyWith(color: colors.inkMute),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(width: space.s),
                    Opacity(
                      opacity: state.isBuildingCase ? 0.42 : 1.0,
                      child: ElevatedButton(
                        onPressed: state.isBuildingCase
                            ? null
                            : () => _triggerCaseBuild(context),
                        style: ElevatedButton.styleFrom(
                          // The CTA is the screen's primary action, so it takes
                          // the action pair — not the banner's semantic tint.
                          backgroundColor: colors.actionPrimaryBg,
                          foregroundColor: colors.actionPrimaryFg,
                          disabledBackgroundColor: colors.actionPrimaryBg,
                          disabledForegroundColor: colors.actionPrimaryFg,
                          padding: density.chip,
                          minimumSize: Size.zero,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(radius.m),
                          ),
                        ),
                        child: Text('გენერაცია', style: type.control),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _triggerCaseBuild(BuildContext context) async {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final cubit = context.read<ConsultationCubit>();
    final casesCubit = context.read<CasesCubit>();
    final creditsCubit = context.read<CreditsCubit>();
    final router = GoRouter.of(context);

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('საქმის გენერაცია'),
        content: const Text(
          'საქმის სრული ანალიზის გენერაციას სჭირდება 3 კრედიტი. გსურთ გაგრძელება?',
        ),
        // Overlay rung (USING §3 / MAPPING §2.4): a dialog is `raised`, not
        // `surface` — the fork used one field for both rungs.
        backgroundColor: colors.raised,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radius.l),
          side: BorderSide(color: colors.lineStrong),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            // `FuzzzyButton.ghost` idle foreground.
            child: Text(
              'გაუქმება',
              style: type.control.copyWith(color: colors.inkMute),
            ),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: colors.actionPrimaryBg,
              foregroundColor: colors.actionPrimaryFg,
              padding: density.snug,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(radius.m),
              ),
            ),
            child: const Text('გენერაცია'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final caseFileData = await cubit.buildCaseFile();

    if (!mounted) return;

    if (caseFileData != null) {
      // Reconcile the credit balance after a billable build.
      creditsCubit.load();
      final newCase = await casesCubit.importCaseData(caseFileData);
      if (newCase != null && mounted) {
        router.go('/cases/${newCase.id}');
      } else if (mounted) {
        FuzzzyToast.show(
          context,
          message: 'საქმის ლოკალურად შენახვა ვერ მოხერხდა',
          kind: FuzzzyToastKind.error,
          qaId: 'consultation.saveFailed',
        );
      }
    } else {
      final failureType = cubit.state.failureType;
      String errMsg = 'საქმის შექმნა ვერ მოხერხდა';
      switch (failureType) {
        case ConsultationFailureType.noCredits:
          errMsg = 'კრედიტები ამოიწურა';
          creditsCubit.load();
        case ConsultationFailureType.rateLimited:
          errMsg = 'მოთხოვნების ლიმიტი ამოიწურა, სცადეთ მოგვიანებით';
        case ConsultationFailureType.network:
          errMsg = 'ინტერნეტთან კავშირი ვერ მოხერხდა';
        case ConsultationFailureType.unauthorized:
          errMsg = 'ავტორიზაცია საჭიროა';
        case _:
          errMsg = 'საქმის შექმნა ვერ მოხერხდა';
      }
      if (mounted) {
        FuzzzyToast.show(
          context,
          message: errMsg,
          kind: FuzzzyToastKind.error,
          qaId: 'consultation.buildFailed',
        );
      }
    }
  }

  void _sendMessage(BuildContext context, ConsultationState state) {
    final text = _messageController.text.trim();
    if (text.isEmpty || state.isSending) return;
    _messageController.clear();
    final creditsCubit = context.read<CreditsCubit>();
    // Refresh the balance once the (billable) turn finishes.
    context
        .read<ConsultationCubit>()
        .sendMessage(text)
        .whenComplete(creditsCubit.load);
  }

  void _showModeSelector(BuildContext context) {
    final cubit = context.read<ConsultationCubit>();
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;
    showModalBottomSheet<void>(
      context: context,
      builder: (_) => SafeArea(
        child: Padding(
          padding: density.dialog,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'წყაროს არჩევა',
                style: type.titleM.copyWith(color: colors.ink),
              ),
              SizedBox(height: space.l),
              _buildModeOption(
                context,
                cubit,
                ChatMode.lawsOnly,
                Icons.menu_book,
                'მხოლოდ კანონები',
                'საკანონმდებლო კოდექსები',
              ),
              SizedBox(height: space.s),
              _buildModeOption(
                context,
                cubit,
                ChatMode.allSources,
                Icons.auto_awesome,
                'ყველა წყარო',
                'კანონები + სასამართლო პრაქტიკა + დიდი პალატა',
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModeOption(
    BuildContext context,
    ConsultationCubit cubit,
    ChatMode mode,
    IconData icon,
    String title,
    String subtitle,
  ) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final radius = context.fuzzzyRadius;
    final isSelected = cubit.state.chatMode == mode;
    return ListTile(
      leading: Icon(icon, color: isSelected ? colors.ink : colors.inkMute),
      title: Text(
        title,
        style: type.titleS.copyWith(color: colors.ink),
      ),
      subtitle: Text(
        subtitle,
        style: type.bodyS.copyWith(color: colors.inkMute),
      ),
      trailing: isSelected ? Icon(Icons.check_circle, color: colors.ink) : null,
      // CONSTANT 1px side; only its colour changes with selection. Fill stays
      // `surface` in both states — the check mark and the ink/inkMute icon are
      // the selection signal, and neither reflows the row.
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(radius.m),
        side: BorderSide(color: isSelected ? colors.lineStrong : colors.line),
      ),
      tileColor: colors.surface,
      onTap: () {
        cubit.switchMode(mode);
        Navigator.of(context).pop();
      },
    );
  }

  void _showCaseSelector(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final cubit = context.read<ConsultationCubit>();

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => SafeArea(
        child: Padding(
          padding: density.dialog,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'საქმის მიმაგრება',
                style: type.titleM.copyWith(color: colors.ink),
              ),
              SizedBox(height: space.xs),
              Text(
                'AI მიიღებს საქმის სრულ კონტექსტს',
                style: type.body.copyWith(color: colors.inkMute),
              ),
              SizedBox(height: space.l),
              // Detach option
              if (cubit.state.hasCaseAttached)
                ListTile(
                  leading: Icon(Icons.link_off, color: colors.destructiveText),
                  title: Text(
                    'საქმის მოხსნა',
                    style: type.titleS.copyWith(color: colors.destructiveText),
                  ),
                  // USING §6 duty 4: the IDLE destructive action is
                  // destructiveText + a destructiveLine outline, never a fill
                  // (the fork tinted the whole tile red at alpha 0.05).
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                    side: BorderSide(color: colors.destructiveLine),
                  ),
                  tileColor: colors.surface,
                  onTap: () {
                    cubit.detachCase();
                    Navigator.pop(context);
                  },
                ),
              if (cubit.state.hasCaseAttached) SizedBox(height: space.s),
              // Case list
              BlocBuilder<CasesCubit, CasesState>(
                builder: (context, casesState) {
                  final cases = casesState.cases;

                  if (casesState.status == StateStatus.loading) {
                    return Padding(
                      padding: EdgeInsets.symmetric(vertical: space.xl),
                      child: const Center(child: CircularProgressIndicator()),
                    );
                  }
                  if (cases.isEmpty) {
                    return Padding(
                      padding: EdgeInsets.symmetric(vertical: space.xl),
                      child: Center(
                        child: Text(
                          'საქმეები არ მოიძებნა',
                          style: type.body.copyWith(color: colors.inkMute),
                        ),
                      ),
                    );
                  }

                  return Column(
                    mainAxisSize: MainAxisSize.min,
                    children: cases.map((caseData) {
                      final isAttached =
                          cubit.state.attachedCaseId == caseData.id;
                      return Padding(
                        padding: EdgeInsets.only(bottom: space.xs),
                        child: ListTile(
                          leading: Icon(
                            isAttached ? Icons.folder : Icons.folder_outlined,
                            color: isAttached ? colors.ink : colors.inkMute,
                          ),
                          title: Text(
                            caseData.title,
                            style: type.titleS.copyWith(color: colors.ink),
                          ),
                          subtitle: Text(
                            caseData.domain.displayNameKa,
                            style: type.bodyS.copyWith(color: colors.inkMute),
                          ),
                          trailing: isAttached
                              ? Icon(
                                  Icons.check_circle,
                                  color: colors.ink,
                                  size: 20,
                                )
                              : null,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(radius.m),
                            side: BorderSide(
                              color: isAttached
                                  ? colors.lineStrong
                                  : colors.line,
                            ),
                          ),
                          tileColor: colors.surface,
                          onTap: () {
                            cubit.attachCase(
                              caseId: caseData.id,
                              caseTitle: caseData.title,
                              caseContext: _buildCaseContextSummary(caseData),
                            );
                            Navigator.pop(context);
                          },
                        ),
                      );
                    }).toList(),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _buildCaseContextSummary(CaseData caseData) {
    final parts = <String>[
      'საქმე: ${caseData.title}',
      'სფერო: ${caseData.domain.displayNameKa}',
    ];
    if (caseData.facts.isNotEmpty) {
      parts.add('ფაქტები: ${caseData.facts.map((f) => f.text).join("; ")}');
    }
    if (caseData.arguments.isNotEmpty) {
      parts.add(
        'არგუმენტები: ${caseData.arguments.map((a) => a.title).join("; ")}',
      );
    }
    if (caseData.linkedArticles.isNotEmpty) {
      parts.add(
        'დაკავშირებული მუხლები: ${caseData.linkedArticles.map((a) => a.title).join("; ")}',
      );
    }
    if (caseData.strategy != null) {
      parts.add('სტრატეგია: ${caseData.strategy!.primaryStrategy}');
    }
    if (caseData.risks.isNotEmpty) {
      parts.add(
        'რისკები: ${caseData.risks.map((r) => r.description).join("; ")}',
      );
    }
    return parts.join('\n');
  }

  void _showHistorySheet(BuildContext context) {
    final cubit = context.read<ConsultationCubit>();

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (_, scrollController) => _HistorySheet(
          cubit: cubit,
          scrollController: scrollController,
          onSelect: (conversationId) {
            Navigator.pop(sheetContext);
            cubit.loadConversation(conversationId);
          },
        ),
      ),
    );
  }

  String _errorMessageKa(ConsultationFailureType? type) => switch (type) {
    ConsultationFailureType.network => 'ინტერნეტთან კავშირი ვერ მოხერხდა',
    ConsultationFailureType.unauthorized => 'ავტორიზაცია საჭიროა',
    ConsultationFailureType.noCredits => 'კრედიტები ამოიწურა',
    ConsultationFailureType.rateLimited =>
      'მოთხოვნების ლიმიტი ამოიწურა, სცადეთ მოგვიანებით',
    ConsultationFailureType.notFound => 'საუბარი ვერ მოიძებნა',
    ConsultationFailureType.serverError => 'სერვერის შეცდომა, სცადეთ ხელახლა',
    ConsultationFailureType.unknown || null => 'უცნობი შეცდომა',
  };
}

/// Which semantic role tints a [_Banner]'s left rule and icon. Mirrors
/// `FuzzzyBannerKind` (containers/fuzzzy_banner.dart) so the M11 swap is a
/// rename — deliberately no `error` rung: red is not a notice (USING §6).
enum _BannerTint { info, success }

/// The inline dismissible notice that sits above the composer.
///
/// Built app-side on roles rather than reaching for `FuzzzyBanner` directly,
/// because this one carries a dismiss affordance whose tap target must clear
/// 44px and the kit's own dismiss is `inkFaint`-only. It copies FuzzzyBanner's
/// recipe exactly: `surface` box, 1px `line` border, `radius.m`, `density.notice`
/// padding, a 3px tinted left rule, and a `bodyS`/`inkMute` message.
class _Banner extends StatelessWidget {
  const _Banner({
    required this.icon,
    required this.tint,
    required this.message,
    required this.onDismiss,
  });

  final IconData icon;
  final _BannerTint tint;
  final String message;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final rule = switch (tint) {
      _BannerTint.info => colors.info,
      _BannerTint.success => colors.success,
    };

    return Container(
      margin: EdgeInsets.symmetric(horizontal: space.l, vertical: space.xs),
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.m),
        border: Border.all(color: colors.line),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Dimension: FuzzzyBanner's 3px left rule.
            Container(width: 3, color: rule),
            Expanded(
              child: Padding(
                padding: density.notice,
                child: Row(
                  children: [
                    Icon(icon, size: 16, color: rule),
                    SizedBox(width: space.s),
                    Expanded(
                      child: Text(
                        message,
                        style: type.bodyS.copyWith(color: colors.inkMute),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    // 44×44 of reach around a 16px glyph WITHOUT making the
                    // notice 44px tall — the fork's bare Icon had a 16×16 tap
                    // target, and a SizedBox(44) here would nearly double the
                    // banner's height above the composer.
                    FuzzzyHitTarget(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: onDismiss,
                        child: Icon(
                          Icons.close,
                          size: 16,
                          color: colors.inkFaint,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Container(
        padding: density.snug,
        // `FuzzzyButton.ghost` shape (harvest/mol.md §2 routes _ActionChip
        // there at M11): surface box, line hairline, `control` label in ink.
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(radius.m),
          border: Border.all(color: colors.line),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: colors.ink),
            SizedBox(width: space.xs),
            Text(
              label,
              // Was a bare TextStyle(fontSize: 13, fontWeight: w600) — that IS
              // `control`, so the literal becomes a role, not a copyWith.
              style: type.control.copyWith(color: colors.ink),
            ),
          ],
        ),
      ),
    );
  }
}

/// Conversation-history sheet. Holds its future so it doesn't refetch on every
/// rebuild, distinguishes empty vs error, and offers a retry on failure.
class _HistorySheet extends StatefulWidget {
  const _HistorySheet({
    required this.cubit,
    required this.scrollController,
    required this.onSelect,
  });

  final ConsultationCubit cubit;
  final ScrollController scrollController;
  final ValueChanged<String> onSelect;

  @override
  State<_HistorySheet> createState() => _HistorySheetState();
}

class _HistorySheetState extends State<_HistorySheet> {
  late Future<ConsultationResult<List<dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.cubit.fetchConversations();
  }

  void _retry() {
    setState(() => _future = widget.cubit.fetchConversations());
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Padding(
      padding: density.dialog,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('ისტორია', style: type.titleM.copyWith(color: colors.ink)),
              IconButton(
                icon: Icon(Icons.close, color: colors.inkMute),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          SizedBox(height: space.l),
          Expanded(
            child: FutureBuilder<ConsultationResult<List<dynamic>>>(
              future: _future,
              builder: (futureContext, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError || snapshot.data is ConsultationFailure) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Oversized state glyph → inkFaint (M4 rule).
                        Icon(Icons.cloud_off, size: 48, color: colors.inkFaint),
                        SizedBox(height: space.m),
                        Text(
                          'ვერ ჩაიტვირთა ისტორია',
                          style: type.body.copyWith(color: colors.inkMute),
                        ),
                        SizedBox(height: space.l),
                        ElevatedButton.icon(
                          onPressed: _retry,
                          icon: const Icon(Icons.refresh, size: 18),
                          label: const Text('ხელახლა ცდა'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: colors.actionPrimaryBg,
                            foregroundColor: colors.actionPrimaryFg,
                            padding: density.snug,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(radius.m),
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                }
                final result =
                    snapshot.data! as ConsultationSuccess<List<dynamic>>;
                final items = result.data;
                if (items.isEmpty) {
                  return Center(
                    child: Text(
                      'ისტორია ცარიელია',
                      style: type.body.copyWith(color: colors.inkMute),
                    ),
                  );
                }
                return ListView.builder(
                  controller: widget.scrollController,
                  itemCount: items.length,
                  itemBuilder: (itemContext, index) {
                    final item = items[index] as Map<String, dynamic>;
                    final title = item['title']?.toString() ?? 'ახალი საუბარი';
                    final phase = item['phase']?.toString() ?? '';
                    final dateStr =
                        item['updated_at']?.toString() ??
                        item['created_at']?.toString() ??
                        '';
                    final date = DateTime.tryParse(dateStr) ?? DateTime.now();

                    return ListTile(
                      leading: Icon(
                        Icons.chat_bubble_outline,
                        color: colors.ink,
                      ),
                      title: Text(
                        title,
                        style: type.titleS.copyWith(color: colors.ink),
                      ),
                      subtitle: Text(
                        '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year} • $phase',
                        // Metadata → `inkFaint` (USING §2.2: timestamps/meta).
                        // NOT the mono `dataS` role, tempting though a date is:
                        // `$phase` is a Georgian word and the mono family has
                        // no Georgian block, so the line would render half in
                        // JetBrains Mono and half in the Noto fallback (M3
                        // rule 4, the same trap as `type.label`).
                        style: type.bodyS.copyWith(color: colors.inkFaint),
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(radius.m),
                      ),
                      onTap: () => widget.onSelect(item['id'].toString()),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
