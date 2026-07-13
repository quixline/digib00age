import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/issue.dart';
import '../services/api_service.dart';
import '../theme/tokens.dart';
import '../widgets/blurred_backdrop.dart';

class IssueDetailScreen extends StatefulWidget {
  final int issueId;
  final ApiService api;

  const IssueDetailScreen({super.key, required this.issueId, required this.api});

  @override
  State<IssueDetailScreen> createState() => _IssueDetailScreenState();
}

class _IssueDetailScreenState extends State<IssueDetailScreen> {
  Issue? _issue;
  bool _loading = true;
  String? _error;
  // Local optimistic overrides (README: "update state immediately, persist
  // via the API") so a tap doesn't wait on a full reload.
  String? _readStatusOverride;
  bool? _favouriteOverride;
  int? _ratingOverride;

  @override
  void initState() {
    super.initState();
    _load(widget.issueId);
  }

  Future<void> _load(int issueId) async {
    setState(() {
      _loading = true;
      _error = null;
      _readStatusOverride = null;
      _favouriteOverride = null;
      _ratingOverride = null;
    });
    try {
      final issue = await widget.api.getIssue(issueId);
      if (mounted) setState(() { _issue = issue; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _toggleRead() {
    final issue = _issue!;
    final isRead = (_readStatusOverride ?? issue.readStatus) == 'read';
    final next = isRead ? 'unread' : 'read';
    setState(() => _readStatusOverride = next);
    if (next == 'read') {
      widget.api.markRead(issue.id);
    } else {
      widget.api.markUnread(issue.id);
    }
  }

  void _toggleFavourite() {
    final issue = _issue!;
    final isFav = _favouriteOverride ?? issue.favorites;
    setState(() => _favouriteOverride = !isFav);
    widget.api.toggleFavorite(issue.id, !isFav);
  }

  void _setRating(int star) {
    final issue = _issue!;
    final current = _ratingOverride ?? issue.personalRating ?? 0;
    final next = current == star ? 0 : star;
    setState(() => _ratingOverride = next);
    widget.api.setRating(issue.id, next);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.redAccent)));
    }

    final issue = _issue!;
    final readStatus = _readStatusOverride ?? issue.readStatus;
    final favourite = _favouriteOverride ?? issue.favorites;
    final rating = _ratingOverride ?? issue.personalRating ?? 0;
    final orientation = MediaQuery.orientationOf(context);
    final backdropHeight = orientation == Orientation.portrait ? 420.0 : 360.0;
    final coverColumnWidth = orientation == Orientation.portrait ? 190.0 : 210.0;
    final coverUrl = '${widget.api.baseUrl}${issue.coverPath}';
    final isSeriesIssue = issue.formatGroup != 'Singles';
    final hasNumber = isSeriesIssue && issue.number != null && issue.number!.isNotEmpty;

    return Stack(
      children: [
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          height: backdropHeight,
          child: BlurredBackdrop(imageUrl: coverUrl),
        ),
        Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: _AccentPill(label: '← Back', onTap: () => Navigator.of(context).pop()),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: coverColumnWidth,
                          child: Column(
                            children: [
                              GestureDetector(
                                onTap: () => Navigator.of(context, rootNavigator: true)
                                    .pushNamed('/reader', arguments: issue.id),
                                child: AspectRatio(
                                  aspectRatio: AppSpacing.coverRatio,
                                  child: Container(
                                    clipBehavior: Clip.antiAlias,
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
                                      border: Border.all(color: AppColors.border),
                                      boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 60, offset: Offset(0, 20))],
                                    ),
                                    child: CachedNetworkImage(
                                      imageUrl: coverUrl,
                                      fit: BoxFit.cover,
                                      errorWidget: (_, _, _) => Container(color: AppColors.surfaceRaised),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 10),
                              _PrimaryButton(
                                label: readStatus == 'read' ? 'Read Again' : (readStatus == 'reading' ? 'Continue Reading' : 'Start Reading'),
                                onTap: () => Navigator.of(context, rootNavigator: true)
                                    .pushNamed('/reader', arguments: issue.id),
                              ),
                              const SizedBox(height: 8),
                              _SecondaryButton(
                                label: readStatus == 'read' ? '✓ Read' : 'Mark as Read',
                                onTap: _toggleRead,
                              ),
                              const SizedBox(height: 8),
                              _SecondaryButton(
                                label: favourite ? '★ In Favourites' : '★ Add to Favourites',
                                onTap: _toggleFavourite,
                              ),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: List.generate(5, (i) {
                                  final starIndex = i + 1;
                                  final filled = starIndex <= rating;
                                  return GestureDetector(
                                    onTap: () => _setRating(starIndex),
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 4),
                                      child: Text(
                                        '★',
                                        style: TextStyle(
                                          fontSize: 22,
                                          color: filled ? AppColors.favouriteGold : const Color(0xFF2A2E36),
                                        ),
                                      ),
                                    ),
                                  );
                                }),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 24),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(issue.displayTitle, style: AppText.titleLarge()),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  if (hasNumber) ...[
                                    _RaisedPill(label: '#${issue.number}'),
                                    const SizedBox(width: 8),
                                  ],
                                  _AccentFilledPill(label: isSeriesIssue ? 'Series' : 'Single'),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Text(
                                [
                                  if (issue.publisher != null) issue.publisher!,
                                  if (issue.year != null) '${issue.year}',
                                  if (issue.language != null) issue.language!,
                                ].join(' · '),
                                style: AppText.secondary(),
                              ),
                              if (issue.genres.isNotEmpty) ...[
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 6,
                                  runSpacing: 6,
                                  children: issue.genres.map((g) => _Tag(label: g)).toList(),
                                ),
                              ],
                              const Divider(height: 36, color: AppColors.border),
                              Text('Summary', style: AppText.eyebrow()),
                              const SizedBox(height: 8),
                              Text(issue.summary ?? '', style: AppText.body()),
                              const Divider(height: 36, color: AppColors.border),
                              Text('Credits', style: AppText.eyebrow()),
                              const SizedBox(height: 8),
                              if (issue.writer != null)
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.baseline,
                                  textBaseline: TextBaseline.alphabetic,
                                  children: [
                                    SizedBox(width: 52, child: Text('Writer', style: AppText.meta())),
                                    Text(
                                      issue.writer!,
                                      style: AppText.label(
                                        size: 14,
                                        weight: FontWeight.w400,
                                        color: AppColors.accentHover,
                                      ).copyWith(decoration: TextDecoration.underline),
                                    ),
                                  ],
                                ),
                              const SizedBox(height: 18),
                              Text(
                                'Rated: ${issue.ageRating ?? 'Unrated'}${issue.pageCount != null ? ' · ${issue.pageCount} pages' : ''}',
                                style: AppText.meta(),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            _PrevNextBar(issue: issue, onNavigate: (id) => _load(id)),
          ],
        ),
      ],
    );
  }
}

class _PrevNextBar extends StatelessWidget {
  final Issue issue;
  final ValueChanged<int> onNavigate;

  const _PrevNextBar({required this.issue, required this.onNavigate});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
      child: Row(
        children: [
          Expanded(
            child: _NavButton(
              label: '← Previous',
              enabled: issue.prevIssueId != null,
              onTap: () => onNavigate(issue.prevIssueId!),
            ),
          ),
          const SizedBox(width: 14),
          Text(
            issue.displayTitle,
            style: AppText.meta(),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: _NavButton(
              label: 'Next →',
              enabled: issue.nextIssueId != null,
              onTap: () => onNavigate(issue.nextIssueId!),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavButton extends StatelessWidget {
  final String label;
  final bool enabled;
  final VoidCallback onTap;

  const _NavButton({required this.label, required this.enabled, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: enabled ? 1 : 0.35,
      child: Material(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
          onTap: enabled ? onTap : null,
          child: Container(
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
            ),
            child: Text(label, style: AppText.label(size: 13)),
          ),
        ),
      ),
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _PrimaryButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.accent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
        onTap: onTap,
        child: Container(
          width: double.infinity,
          height: 36,
          alignment: Alignment.center,
          child: Text(label, style: AppText.label(size: 13, color: Colors.white), textAlign: TextAlign.center),
        ),
      ),
    );
  }
}

class _SecondaryButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _SecondaryButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surfaceRaised,
      borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
        onTap: onTap,
        child: Container(
          width: double.infinity,
          height: 36,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
          ),
          child: Text(label, style: AppText.label(size: 13), textAlign: TextAlign.center),
        ),
      ),
    );
  }
}

class _AccentPill extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _AccentPill({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.accent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          child: Text(label, style: AppText.label(size: 13, color: Colors.white)),
        ),
      ),
    );
  }
}

class _RaisedPill extends StatelessWidget {
  final String label;
  const _RaisedPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.surfaceRaised,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
      ),
      child: Text(label, style: AppText.label(size: 12, weight: FontWeight.w700)),
    );
  }
}

class _AccentFilledPill extends StatelessWidget {
  final String label;
  const _AccentFilledPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.accent,
        borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
      ),
      child: Text(label, style: AppText.label(size: 12, weight: FontWeight.w700, color: Colors.white)),
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  const _Tag({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceRaised,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
      ),
      child: Text(label, style: AppText.meta(size: 12, color: AppColors.textSecondary)),
    );
  }
}
