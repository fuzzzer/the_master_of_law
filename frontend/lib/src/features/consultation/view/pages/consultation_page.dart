import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/core/core.dart';
import 'package:themasteroflaw/src/features/consultation/consultation.dart';
import 'package:themasteroflaw/src/features/laws/laws.dart';

class ConsultationPage extends StatefulWidget {
  const ConsultationPage({super.key});

  @override
  State<ConsultationPage> createState() => _ConsultationPageState();
}

class _ConsultationPageState extends State<ConsultationPage> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
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
        title: Text('AI კონსულტაცია',
            style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
        actions: [
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
                        color: state.chatMode == ChatMode.lawsOnly
                            ? uiColors.accentColor : uiColors.secondaryTextColor,
                      ),
                      const SizedBox(width: 4),
                      Text(state.chatMode.labelKa,
                          style: uiTextStyles.caption11.copyWith(
                            color: state.chatMode == ChatMode.lawsOnly
                                ? uiColors.accentColor : uiColors.secondaryTextColor,
                            fontWeight: FontWeight.w600,
                          )),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: BlocConsumer<ConsultationCubit, ConsultationState>(
        listenWhen: (prev, curr) => prev.messages.length != curr.messages.length,
        listener: (context, state) => _scrollToBottom(),
        builder: (context, state) {
          if (state.status == StateStatus.initial) return _buildWelcome(context, state);
          if (state.status == StateStatus.loading && state.messages.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return Column(
            children: [
              Expanded(child: _buildMessageList(context, state)),
              _buildInputBar(context, state),
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
            Text('AI კონსულტაცია',
                style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
            const SizedBox(height: 8),
            Text('დაუსვით იურიდიული კითხვა',
                style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                textAlign: TextAlign.center),
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
            Icon(mode == ChatMode.lawsOnly ? Icons.menu_book : Icons.auto_awesome,
                color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor),
            const SizedBox(height: 4),
            Text(mode.labelKa, style: uiTextStyles.caption11.copyWith(
              color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList(BuildContext context, ConsultationState state) {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: state.messages.length + (state.isSending ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == state.messages.length && state.isSending) return _buildTypingIndicator(context);
        return _buildMessageBubble(context, state.messages[index]);
      },
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
        child: Row(children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(_errorMessageKa(message.failureType),
              style: uiTextStyles.body14.copyWith(color: Colors.red))),
        ]),
      );
    }

    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: message.isUser
              ? uiColors.accentColor.withValues(alpha: 0.15)
              : uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(14),
          border: message.isUser ? Border.all(color: uiColors.accentColor.withValues(alpha: 0.2)) : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SelectableText(message.text,
                style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor, height: 1.5)),
            if (message.citations != null && message.citations!.isNotEmpty) ...[
              const SizedBox(height: 10),
              Divider(color: uiColors.secondaryTextColor.withValues(alpha: 0.15), height: 1),
              const SizedBox(height: 8),
              ...message.citations!.map((c) => _buildCitationChip(context, c)),
            ],
          ],
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
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.article_outlined, size: 14, color: Color(0xFF1565C0)),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              citation.articleTitle.isNotEmpty ? citation.articleTitle : 'მუხლი ${citation.articleId}',
              style: uiTextStyles.caption11.copyWith(
                  color: const Color(0xFF1565C0), decoration: TextDecoration.underline),
              maxLines: 1, overflow: TextOverflow.ellipsis,
            ),
          ),
        ]),
      ),
    );
  }

  void _navigateToArticle(BuildContext context, CitationData citation) {
    Navigator.of(context).push(MaterialPageRoute<void>(
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
    ));
  }

  Widget _buildTypingIndicator(BuildContext context) {
    final uiColors = context.uiColors;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: uiColors.backgroundSecondaryColor, borderRadius: BorderRadius.circular(14)),
        child: Row(mainAxisSize: MainAxisSize.min, children: List.generate(3, (i) => Container(
          margin: const EdgeInsets.symmetric(horizontal: 2), width: 8, height: 8,
          decoration: BoxDecoration(color: uiColors.secondaryTextColor.withValues(alpha: 0.4), shape: BoxShape.circle),
        ))),
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
      child: Row(children: [
        Expanded(child: TextField(
          controller: _messageController,
          style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
          decoration: InputDecoration(
            hintText: 'დაწერეთ კითხვა...', border: InputBorder.none,
            hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          ),
          maxLines: 4, minLines: 1, textInputAction: TextInputAction.send,
          onSubmitted: (_) => _sendMessage(context, state),
        )),
        IconButton(
          icon: Icon(Icons.send, color: state.isSending
              ? uiColors.secondaryTextColor.withValues(alpha: 0.3) : uiColors.accentColor),
          onPressed: state.isSending ? null : () => _sendMessage(context, state),
        ),
      ]),
    );
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
    showModalBottomSheet<void>(context: context, builder: (_) => SafeArea(
      child: Padding(padding: const EdgeInsets.all(20), child: Column(
        mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('წყაროს არჩევა', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 16),
          _buildModeOption(context, cubit, ChatMode.lawsOnly, Icons.menu_book, 'მხოლოდ კანონები', 'საკანონმდებლო კოდექსები'),
          const SizedBox(height: 8),
          _buildModeOption(context, cubit, ChatMode.allSources, Icons.auto_awesome, 'ყველა წყარო', 'კანონები + სასამართლო პრაქტიკა + დიდი პალატა'),
        ],
      )),
    ));
  }

  Widget _buildModeOption(BuildContext context, ConsultationCubit cubit, ChatMode mode, IconData icon, String title, String subtitle) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final isSelected = cubit.state.chatMode == mode;
    return ListTile(
      leading: Icon(icon, color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor),
      title: Text(title, style: uiTextStyles.bodyBold14.copyWith(color: isSelected ? uiColors.accentColor : uiColors.primaryTextColor)),
      subtitle: Text(subtitle, style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor)),
      trailing: isSelected ? Icon(Icons.check_circle, color: uiColors.accentColor) : null,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      tileColor: isSelected ? uiColors.accentColor.withValues(alpha: 0.08) : uiColors.backgroundSecondaryColor,
      onTap: () { cubit.switchMode(mode); Navigator.of(context).pop(); },
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
