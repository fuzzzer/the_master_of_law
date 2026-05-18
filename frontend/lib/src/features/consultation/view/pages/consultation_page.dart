import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/cases/cases.dart';
import 'package:themasteroflaw/src/features/consultation/consultation.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';
import 'package:url_launcher/url_launcher.dart';

class ConsultationPage extends StatefulWidget {
  const ConsultationPage({super.key});

  @override
  State<ConsultationPage> createState() => _ConsultationPageState();
}

class _ConsultationPageState extends State<ConsultationPage> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  bool _actionChipsDismissed = false;

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  bool _isNearBottom() {
    if (!_scrollController.hasClients) return true;
    final pos = _scrollController.position;
    // Consider "near bottom" if within 150px of the end (forward list scrolls to maxExtent)
    // For reversed list, bottom is position 0 — but we keep this for the reversed case too.
    return pos.pixels <= 150.0;
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      // Reversed list: bottom = position 0. Only jump if user is already near bottom.
      if (_isNearBottom()) {
        _scrollController.animateTo(
          0,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text('AI კონსულტაცია', style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
        leading: IconButton(
          icon: const Icon(Icons.history),
          onPressed: () => _showHistorySheet(context),
        ),
        actions: [
          BlocBuilder<ConsultationCubit, ConsultationState>(
            builder: (context, state) {
              if (state.status == StateStatus.initial) return const SizedBox.shrink();
              return IconButton(
                icon: Icon(Icons.add_comment_outlined, color: uiColors.primaryTextColor),
                tooltip: 'ახალი საუბარი',
                onPressed: () => context.read<ConsultationCubit>().reset(),
              );
            },
          ),
          BlocBuilder<ConsultationCubit, ConsultationState>(
            builder: (context, state) {
              //TODO enable sooner if needed
              if (state.status == StateStatus.initial || state.messages.length < 6) return const SizedBox.shrink();
              return IconButton(
                icon: Icon(Icons.description_outlined, color: uiColors.primaryTextColor),
                tooltip: 'საქმის გენერაცია',
                onPressed: state.isBuildingCase ? null : () => _triggerCaseBuild(context),
              );
            },
          ),
          BlocBuilder<ConsultationCubit, ConsultationState>(
            buildWhen: (prev, curr) => prev.chatMode != curr.chatMode,
            builder: (context, state) {
              return GestureDetector(
                onTap: () => _showModeSelector(context),
                child: Container(
                  margin: const EdgeInsets.only(right: 12),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: state.chatMode == ChatMode.lawsOnly
                        ? uiColors.accentColor.withValues(alpha: 0.15)
                        : uiColors.secondaryTextColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: state.chatMode == ChatMode.lawsOnly
                          ? uiColors.accentColor.withValues(alpha: 0.3)
                          : uiColors.secondaryTextColor.withValues(alpha: 0.2),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        state.chatMode == ChatMode.lawsOnly ? Icons.menu_book : Icons.auto_awesome,
                        size: 14,
                        color: state.chatMode == ChatMode.lawsOnly ? uiColors.accentColor : uiColors.secondaryTextColor,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        state.chatMode.labelKa,
                        style: uiTextStyles.caption11.copyWith(
                          color: state.chatMode == ChatMode.lawsOnly
                              ? uiColors.accentColor
                              : uiColors.secondaryTextColor,
                          fontWeight: FontWeight.w600,
                        ),
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
          if (curr.streamingMessageId != null && curr.messages.isNotEmpty) {
            final prevMsg = prev.messages.where((m) => m.id == curr.streamingMessageId).firstOrNull;
            final currMsg = curr.messages.where((m) => m.id == curr.streamingMessageId).firstOrNull;
            if (prevMsg != null && currMsg != null && prevMsg.text.length != currMsg.text.length) {
              return true;
            }
          }
          return false;
        },
        listener: (context, state) => _scrollToBottom(),
        builder: (context, state) {
          if (state.status == StateStatus.initial) return _buildWelcome(context, state);
          if (state.status == StateStatus.loading && state.messages.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return Stack(
            children: [
              Column(
                children: [
                  Expanded(child: _buildMessageList(context, state)),
                  if (state.caseAnalysisReady && !state.hasCaseAttached) _buildCaseReadyBanner(context, state),
                  if (state.hasCaseAttached) _buildAttachedCaseBanner(context, state),
                  _buildInputBar(context, state),
                ],
              ),
              if (state.isBuildingCase)
                ColoredBox(
                  color: Colors.black.withValues(alpha: 0.3),
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: uiColors.backgroundSecondaryColor,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const CircularProgressIndicator(),
                          const SizedBox(height: 16),
                          Text(
                            'საქმე მზადდება...',
                            style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'ეს შეიძლება 30-60 წამი გაგრძელდეს',
                            style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology, size: 64, color: uiColors.accentColor.withValues(alpha: 0.4)),
            const SizedBox(height: 20),
            Text('AI კონსულტაცია', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
            const SizedBox(height: 8),
            Text(
              'დაუსვით იურიდიული კითხვა',
              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildModeButton(context, ChatMode.lawsOnly, state.chatMode),
                const SizedBox(width: 12),
                _buildModeButton(context, ChatMode.allSources, state.chatMode),
              ],
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => context.read<ConsultationCubit>().startConversation(),
              icon: const Icon(Icons.chat),
              label: const Text('დაწყება'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModeButton(BuildContext context, ChatMode mode, ChatMode currentMode) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final isSelected = mode == currentMode;
    return GestureDetector(
      onTap: () => context.read<ConsultationCubit>().switchMode(mode),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? uiColors.accentColor.withValues(alpha: 0.15) : uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor.withValues(alpha: 0.2),
          ),
        ),
        child: Column(
          children: [
            Icon(
              mode == ChatMode.lawsOnly ? Icons.menu_book : Icons.auto_awesome,
              color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
            ),
            const SizedBox(height: 4),
            Text(
              mode.labelKa,
              style: uiTextStyles.caption11.copyWith(
                color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList(BuildContext context, ConsultationState state) {
    // Show action chips after first AI response (2 messages: user + AI)
    final showChips =
        !_actionChipsDismissed && state.messages.length >= 2 && !state.isSending && state.messages.last.isUser == false;

    // We only show the typing indicator if we're sending and haven't received any text yet
    final streamingMsg = state.streamingMessageId != null 
        ? state.messages.where((m) => m.id == state.streamingMessageId).firstOrNull 
        : null;
    final showTypingIndicator = state.isSending && (streamingMsg == null || streamingMsg.text.isEmpty);

    // Filter out the empty streaming message if we're showing the typing indicator instead
    final displayMessages = state.messages.where((m) => !(m.id == state.streamingMessageId && m.text.isEmpty)).toList();

    return ListView.builder(
      controller: _scrollController,
      reverse: true,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      // Item order (reversed list): index 0 = visually at bottom
      //   [0]           typing indicator (if active)
      //   [1..N]        messages newest-first
      //   [N+1]         action chips (if visible)
      itemCount: displayMessages.length + (showTypingIndicator ? 1 : 0) + (showChips ? 1 : 0),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'როგორ გსურთ გაგრძელება?',
            style: uiTextStyles.labelBold12.copyWith(color: uiColors.secondaryTextColor),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _ActionChip(
                icon: Icons.quiz_outlined,
                label: '🔍 დამაზუსტე',
                color: uiColors.accentColor,
                onTap: () {
                  setState(() => _actionChipsDismissed = true);
                  context.read<ConsultationCubit>().sendMessage(
                    'გთხოვ, დამისვი დამაზუსტებელი კითხვები ჩემი სიტუაციის შესახებ, რომ უკეთესად გამიგო და დამეხმარო.',
                  );
                },
              ),
              _ActionChip(
                icon: Icons.auto_awesome,
                label: '📊 სრული ანალიზი',
                color: const Color(0xFF2ECC71),
                onTap: () {
                  setState(() => _actionChipsDismissed = true);
                  context.read<ConsultationCubit>().sendMessage(
                    'გთხოვ, გამიკეთე ჩემი სიტუაციის სრული იურიდიული ანალიზი — ყველა შესაბამისი კანონის მუხლით, სტრატეგიით და რეკომენდაციებით.',
                  );
                },
              ),
              _ActionChip(
                icon: Icons.chat_bubble_outline,
                label: '💬 გავაგრძელო',
                color: uiColors.secondaryTextColor,
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    if (message.isError) {
      return Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.red.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.red.withValues(alpha: 0.2)),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Text(_errorMessageKa(message.failureType), style: uiTextStyles.body14.copyWith(color: Colors.red)),
            ),
          ],
        ),
      );
    }

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: () {
          Clipboard.setData(ClipboardData(text: message.text));
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('გადაკოპირებულია'),
              duration: Duration(seconds: 1),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: message.isUser ? uiColors.accentColor.withValues(alpha: 0.15) : uiColors.backgroundSecondaryColor,
            borderRadius: BorderRadius.circular(14),
            border: message.isUser ? Border.all(color: uiColors.accentColor.withValues(alpha: 0.2)) : null,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(
                message.text,
                style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor, height: 1.5),
              ),
              if (message.citations != null && message.citations!.isNotEmpty) ...[
                const SizedBox(height: 10),
                Divider(color: uiColors.secondaryTextColor.withValues(alpha: 0.15), height: 1),
                const SizedBox(height: 8),
                ...message.citations!.map((c) => _buildCitationChip(context, c)),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCitationChip(BuildContext context, CitationData citation) {
    final uiTextStyles = context.uiTextStyles;
    return GestureDetector(
      onTap: () => _navigateToArticle(context, citation),
      child: Container(
        margin: const EdgeInsets.only(bottom: 4),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF1565C0).withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xFF1565C0).withValues(alpha: 0.15)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.article_outlined, size: 14, color: Color(0xFF1565C0)),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                citation.articleTitle.isNotEmpty ? citation.articleTitle : 'მუხლი ${citation.articleId}',
                style: uiTextStyles.caption11.copyWith(
                  color: const Color(0xFF1565C0),
                  decoration: TextDecoration.underline,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }

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
            repository: LawsRepository(remoteDataSource: LawsRemoteDataSource()),
          )..loadArticle(citation.articleId),
          child: LawArticlePage(
            articleId: citation.articleId,
            articleTitle: citation.articleTitle.isNotEmpty ? citation.articleTitle : 'მუხლი ${citation.articleId}',
            codeName: citation.codeTitle,
          ),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator(BuildContext context, ConsultationState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: uiColors.backgroundSecondaryColor, borderRadius: BorderRadius.circular(14)),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(
                3,
                (i) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: uiColors.secondaryTextColor.withValues(alpha: 0.4),
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
            if (state.streamingStatus != null) ...[
              const SizedBox(width: 12),
              Flexible(
                child: Text(
                  state.streamingStatus!,
                  style: uiTextStyles.caption11.copyWith(
                    color: uiColors.secondaryTextColor,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInputBar(BuildContext context, ConsultationState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Container(
      padding: EdgeInsets.fromLTRB(16, 8, 8, MediaQuery.of(context).padding.bottom + 8),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        border: Border(top: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.1))),
      ),
      child: Row(
        children: [
          // Case attachment button
          IconButton(
            icon: Icon(
              state.hasCaseAttached ? Icons.folder : Icons.folder_open_outlined,
              color: state.hasCaseAttached ? uiColors.accentColor : uiColors.secondaryTextColor,
              size: 22,
            ),
            onPressed: () => _showCaseSelector(context),
            tooltip: 'საქმის მიმაგრება',
          ),
          Expanded(
            child: TextField(
              controller: _messageController,
              style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
              decoration: InputDecoration(
                hintText: 'დაწერეთ კითხვა...',
                border: InputBorder.none,
                hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              ),
              maxLines: 4,
              minLines: 1,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(context, state),
            ),
          ),
          IconButton(
            icon: Icon(
              Icons.send,
              color: state.isSending ? uiColors.secondaryTextColor.withValues(alpha: 0.3) : uiColors.accentColor,
            ),
            onPressed: state.isSending ? null : () => _sendMessage(context, state),
          ),
        ],
      ),
    );
  }

  Widget _buildAttachedCaseBanner(BuildContext context, ConsultationState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: uiColors.accentColor.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Icon(Icons.folder, size: 16, color: uiColors.accentColor),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '📁 ${state.attachedCaseTitle ?? 'საქმე'}',
              style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          GestureDetector(
            onTap: () => context.read<ConsultationCubit>().detachCase(),
            child: Icon(Icons.close, size: 16, color: uiColors.secondaryTextColor),
          ),
        ],
      ),
    );
  }

  Widget _buildCaseReadyBanner(BuildContext context, ConsultationState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF2ECC71).withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF2ECC71).withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle_outline, color: Color(0xFF2ECC71), size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'საკმარისი კონტექსტი შეგროვდა',
                  style: uiTextStyles.bodyBold14.copyWith(color: const Color(0xFF2ECC71)),
                ),
                const SizedBox(height: 2),
                Text(
                  'AI მზადაა საქმის დასაგენერირებლად',
                  style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                ),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: state.isBuildingCase ? null : () => _triggerCaseBuild(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2ECC71),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              minimumSize: Size.zero,
            ),
            child: const Text('გენერაცია'),
          ),
        ],
      ),
    );
  }

  Future<void> _triggerCaseBuild(BuildContext context) async {
    final uiColors = context.uiColors;
    final cubit = context.read<ConsultationCubit>();
    final casesCubit = context.read<CasesCubit>();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('საქმის გენერაცია'),
        content: const Text('საქმის სრული ანალიზის გენერაციას სჭირდება 3 კრედიტი. გსურთ გაგრძელება?'),
        backgroundColor: uiColors.backgroundSecondaryColor,
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('გაუქმება', style: TextStyle(color: uiColors.secondaryTextColor)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: uiColors.accentColor),
            child: const Text('გენერაცია'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final caseFileData = await cubit.buildCaseFile();

    if (!mounted) return;

    if (caseFileData != null) {
      final newCase = await casesCubit.importCaseData(caseFileData);
      if (newCase != null && mounted) {
        context.go('/cases/${newCase.id}');
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('საქმის ლოკალურად შენახვა ვერ მოხერხდა')),
        );
      }
    } else {
      final failureType = cubit.state.failureType;
      String errMsg = 'საქმის შექმნა ვერ მოხერხდა';
      if (failureType == ConsultationFailureType.noCredits) {
        errMsg = 'კრედიტები ამოიწურა';
      }
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errMsg)));
    }
  }

  void _sendMessage(BuildContext context, ConsultationState state) {
    final text = _messageController.text.trim();
    if (text.isEmpty || state.isSending) return;
    _messageController.clear();
    context.read<ConsultationCubit>().sendMessage(text);
  }

  void _showModeSelector(BuildContext context) {
    final cubit = context.read<ConsultationCubit>();
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    showModalBottomSheet<void>(
      context: context,
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('წყაროს არჩევა', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
              const SizedBox(height: 16),
              _buildModeOption(
                context,
                cubit,
                ChatMode.lawsOnly,
                Icons.menu_book,
                'მხოლოდ კანონები',
                'საკანონმდებლო კოდექსები',
              ),
              const SizedBox(height: 8),
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
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final isSelected = cubit.state.chatMode == mode;
    return ListTile(
      leading: Icon(icon, color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor),
      title: Text(
        title,
        style: uiTextStyles.bodyBold14.copyWith(color: isSelected ? uiColors.accentColor : uiColors.primaryTextColor),
      ),
      subtitle: Text(subtitle, style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
      trailing: isSelected ? Icon(Icons.check_circle, color: uiColors.accentColor) : null,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      tileColor: isSelected ? uiColors.accentColor.withValues(alpha: 0.08) : uiColors.backgroundSecondaryColor,
      onTap: () {
        cubit.switchMode(mode);
        Navigator.of(context).pop();
      },
    );
  }

  void _showCaseSelector(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final cubit = context.read<ConsultationCubit>();

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('საქმის მიმაგრება', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
              const SizedBox(height: 4),
              Text(
                'AI მიიღებს საქმის სრულ კონტექსტს',
                style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
              ),
              const SizedBox(height: 16),
              // Detach option
              if (cubit.state.hasCaseAttached)
                ListTile(
                  leading: Icon(Icons.link_off, color: uiColors.errorColor),
                  title: Text('საქმის მოხსნა', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.errorColor)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  tileColor: uiColors.errorColor.withValues(alpha: 0.05),
                  onTap: () {
                    cubit.detachCase();
                    Navigator.pop(context);
                  },
                ),
              if (cubit.state.hasCaseAttached) const SizedBox(height: 8),
              // Case list
              BlocBuilder<CasesCubit, CasesState>(
                builder: (context, casesState) {
                  final cases = casesState.cases;

                  if (casesState.status == StateStatus.loading) {
                    return const Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: Center(child: CircularProgressIndicator()),
                    );
                  }
                  if (cases.isEmpty) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Center(
                        child: Text(
                          'საქმეები არ მოიძებნა',
                          style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                        ),
                      ),
                    );
                  }

                  return Column(
                    mainAxisSize: MainAxisSize.min,
                    children: cases.map((caseData) {
                      final isAttached = cubit.state.attachedCaseId == caseData.id;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: ListTile(
                          leading: Icon(
                            isAttached ? Icons.folder : Icons.folder_outlined,
                            color: isAttached ? uiColors.accentColor : uiColors.secondaryTextColor,
                          ),
                          title: Text(
                            caseData.title,
                            style: uiTextStyles.bodyBold14.copyWith(
                              color: isAttached ? uiColors.accentColor : uiColors.primaryTextColor,
                            ),
                          ),
                          subtitle: Text(
                            caseData.domain.displayNameKa,
                            style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                          ),
                          trailing: isAttached ? Icon(Icons.check_circle, color: uiColors.accentColor, size: 20) : null,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          tileColor: isAttached
                              ? uiColors.accentColor.withValues(alpha: 0.08)
                              : uiColors.backgroundSecondaryColor,
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
      parts.add('არგუმენტები: ${caseData.arguments.map((a) => a.title).join("; ")}');
    }
    if (caseData.linkedArticles.isNotEmpty) {
      parts.add('დაკავშირებული მუხლები: ${caseData.linkedArticles.map((a) => a.title).join("; ")}');
    }
    if (caseData.strategy != null) {
      parts.add('სტრატეგია: ${caseData.strategy!.primaryStrategy}');
    }
    if (caseData.risks.isNotEmpty) {
      parts.add('რისკები: ${caseData.risks.map((r) => r.description).join("; ")}');
    }
    return parts.join('\n');
  }

  void _showHistorySheet(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final cubit = context.read<ConsultationCubit>();

    // We instantiate a new repository just for this sheet to fetch history
    final tempRepo = ConsultationRepository(remoteDataSource: ConsultationRemoteDataSource());

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (_, scrollController) => Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('ისტორია', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(sheetContext)),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: FutureBuilder<ConsultationResult<List<dynamic>>>(
                  future: tempRepo.getConversations(),
                  builder: (futureContext, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError || snapshot.data is ConsultationFailure) {
                      return Center(
                        child: Text('ვერ ჩაიტვირთა ისტორია', style: uiTextStyles.body14.copyWith(color: Colors.red)),
                      );
                    }
                    final result = snapshot.data! as ConsultationSuccess<List<dynamic>>;
                    final items = result.data;
                    if (items.isEmpty) {
                      return Center(
                        child: Text(
                          'ისტორია ცარიელია',
                          style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                        ),
                      );
                    }
                    return ListView.builder(
                      controller: scrollController,
                      itemCount: items.length,
                      itemBuilder: (itemContext, index) {
                        final item = items[index] as Map<String, dynamic>;
                        final title = item['title']?.toString() ?? 'ახალი საუბარი';
                        final phase = item['phase']?.toString() ?? '';
                        final dateStr = item['updated_at']?.toString() ?? item['created_at']?.toString() ?? '';
                        final date = DateTime.tryParse(dateStr) ?? DateTime.now();

                        return ListTile(
                          leading: Icon(Icons.chat_bubble_outline, color: uiColors.accentColor),
                          title: Text(title, style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
                          subtitle: Text(
                            '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year} • $phase',
                            style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                          ),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          onTap: () {
                            Navigator.pop(sheetContext);
                            cubit.loadConversation(item['id'].toString());
                          },
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _errorMessageKa(ConsultationFailureType? type) => switch (type) {
    ConsultationFailureType.network => 'ინტერნეტთან კავშირი ვერ მოხერხდა',
    ConsultationFailureType.unauthorized => 'ავტორიზაცია საჭიროა',
    ConsultationFailureType.noCredits => 'კრედიტები ამოიწურა',
    ConsultationFailureType.notFound => 'საუბარი ვერ მოიძებნა',
    ConsultationFailureType.serverError => 'სერვერის შეცდომა, სცადეთ ხელახლა',
    ConsultationFailureType.unknown || null => 'უცნობი შეცდომა',
  };
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
