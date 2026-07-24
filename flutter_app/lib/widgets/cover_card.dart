// Grid + list cover card shared by Home strips and Browse. Both callers map
// their own source data (series-level /api/library or issue-level
// /api/home/strips cards) into this one small view-model.
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../theme/tokens.dart';

class CoverCardData {
  final String title;
  final String meta;
  final String? coverUrl; // null = no cover (e.g. an empty folder tile)
  final String state; // 'unread' | 'progress' | 'read'
  final int progressPercent;
  final bool favourite;
  final int unreadCount; // 0 = no badge
  final String? summary; // list view only
  final String? genresLabel; // list view only
  final String? credLabel; // list view only ("Publisher · Writer")
  final VoidCallback onTap;

  const CoverCardData({
    required this.title,
    required this.meta,
    required this.coverUrl,
    required this.state,
    this.progressPercent = 0,
    this.favourite = false,
    this.unreadCount = 0,
    this.summary,
    this.genresLabel,
    this.credLabel,
    required this.onTap,
  });
}

class CoverCard extends StatefulWidget {
  final CoverCardData data;
  const CoverCard({super.key, required this.data});

  @override
  State<CoverCard> createState() => _CoverCardState();
}

class _CoverCardState extends State<CoverCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final d = widget.data;
    final colors = AppColors.of(context);
    final text = AppText.of(context);
    final isRead = d.state == 'read';
    final isProgress = d.state == 'progress';

    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: d.onTap,
        child: AnimatedContainer(
          duration: AppMotion.railDuration,
          curve: AppMotion.railCurve,
          transform: Matrix4.translationValues(
            0,
            _hover ? -AppMotion.lift : 0,
            0,
          ),
          padding: const EdgeInsets.fromLTRB(3, 3, 3, 8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
            border: Border.all(
              color: _hover ? colors.accent : colors.cardBorder,
              width: 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AspectRatio(
                aspectRatio: AppSpacing.coverRatio,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppSpacing.radiusLg - 3),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      if (d.coverUrl == null)
                        Container(
                          color: colors.surfaceRaised,
                          child: Icon(
                            Icons.menu_book_outlined,
                            color: colors.textMuted,
                            size: 32,
                          ),
                        )
                      else
                        CachedNetworkImage(
                          imageUrl: d.coverUrl!,
                          fit: BoxFit.cover,
                          errorWidget: (_, _, _) => Container(
                            color: colors.surfaceRaised,
                            child: Icon(
                              Icons.menu_book_outlined,
                              color: colors.textMuted,
                              size: 32,
                            ),
                          ),
                        ),
                      if (isProgress) ...[
                        Positioned(
                          left: 0,
                          right: 0,
                          bottom: 0,
                          height: 56,
                          child: Container(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.bottomCenter,
                                end: Alignment.topCenter,
                                colors: [
                                  colors.readGreen.withValues(alpha: 0.85),
                                  colors.readGreen.withValues(alpha: 0.0),
                                ],
                              ),
                            ),
                          ),
                        ),
                        Positioned(
                          left: 0,
                          right: 0,
                          bottom: 0,
                          child: Container(height: 3, color: colors.readGreen),
                        ),
                        Positioned(
                          left: 6,
                          right: 6,
                          bottom: 6,
                          child: Text(
                            '${d.progressPercent}% Read',
                            style: text.label(size: 11, color: Colors.white),
                          ),
                        ),
                      ],
                      if (d.favourite)
                        Positioned(
                          top: 6,
                          left: 6,
                          child: Container(
                            padding: const EdgeInsets.all(2),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.35),
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.black, width: 1),
                            ),
                            child: const Text(
                              '♥',
                              style: TextStyle(
                                color: Color(0xFFE0435C),
                                fontSize: 13,
                                height: 1,
                              ),
                            ),
                          ),
                        ),
                      if (isRead)
                        Positioned(
                          top: 6,
                          right: 6,
                          child: Container(
                            width: 14,
                            height: 14,
                            decoration: BoxDecoration(
                              color: colors.readGreen,
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 2),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        d.title,
                        style: text.label(size: 13),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      d.meta,
                      style: text.meta(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class CoverListRow extends StatefulWidget {
  final CoverCardData data;
  const CoverListRow({super.key, required this.data});

  @override
  State<CoverListRow> createState() => _CoverListRowState();
}

class _CoverListRowState extends State<CoverListRow> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final d = widget.data;
    final colors = AppColors.of(context);
    final text = AppText.of(context);
    final isRead = d.state == 'read';
    final isProgress = d.state == 'progress';

    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: d.onTap,
        child: AnimatedContainer(
          duration: AppMotion.railDuration,
          curve: AppMotion.railCurve,
          transform: Matrix4.translationValues(
            0,
            _hover ? -AppMotion.lift : 0,
            0,
          ),
          decoration: BoxDecoration(
            color: colors.surfaceCard,
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            border: Border.all(
              color: _hover ? colors.accent : colors.cardBorder,
              width: 1,
            ),
          ),
          clipBehavior: Clip.antiAlias,
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(
                  width: 96,
                  child: Padding(
                    padding: const EdgeInsets.all(3),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(
                        AppSpacing.radiusMd - 3,
                      ),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          if (d.coverUrl == null)
                            Container(
                              color: colors.surfaceRaised,
                              child: Icon(
                                Icons.menu_book_outlined,
                                color: colors.textMuted,
                              ),
                            )
                          else
                            CachedNetworkImage(
                              imageUrl: d.coverUrl!,
                              fit: BoxFit.cover,
                              errorWidget: (_, _, _) => Container(
                                color: colors.surfaceRaised,
                                child: Icon(
                                  Icons.menu_book_outlined,
                                  color: colors.textMuted,
                                ),
                              ),
                            ),
                          if (isRead)
                            Container(
                              color: colors.readGreen.withValues(alpha: 0.5),
                            ),
                          if (d.favourite)
                            Positioned(
                              top: 6,
                              left: 6,
                              child: Container(
                                padding: const EdgeInsets.all(2),
                                decoration: BoxDecoration(
                                  color: Colors.black.withValues(alpha: 0.35),
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: Colors.black,
                                    width: 1,
                                  ),
                                ),
                                child: const Text(
                                  '♥',
                                  style: TextStyle(
                                    color: Color(0xFFE0435C),
                                    fontSize: 13,
                                    height: 1,
                                  ),
                                ),
                              ),
                            ),
                          if (isProgress)
                            Positioned(
                              left: 0,
                              right: 0,
                              bottom: 0,
                              child: Container(
                                height: 32,
                                color: Colors.black.withValues(alpha: 0.35),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          d.title,
                          style: text.label(size: 14),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 3),
                        Text(
                          d.meta,
                          style: text.meta(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (d.summary != null && d.summary!.isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Text(
                            d.summary!,
                            style: text.meta(),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                        if (d.genresLabel != null &&
                            d.genresLabel!.isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Text(
                            d.genresLabel!,
                            style: text.secondary(size: 12),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                        if (d.credLabel != null && d.credLabel!.isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Text(
                            d.credLabel!,
                            style: text.meta(),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                        if (isProgress) ...[
                          const SizedBox(height: 3),
                          Text(
                            '${d.progressPercent}% Read',
                            style: text.label(size: 12, color: Colors.white),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
