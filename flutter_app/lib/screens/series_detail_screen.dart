import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';
import '../services/download_service.dart';
import '../theme/tokens.dart';
import '../widgets/status_button.dart';
import '../widgets/blurred_backdrop.dart';

class SeriesDetailScreen extends StatefulWidget {
  final int anchorId;
  final ApiService api;
  final DownloadService downloads;

  const SeriesDetailScreen({
    super.key,
    required this.anchorId,
    required this.api,
    required this.downloads,
  });

  @override
  State<SeriesDetailScreen> createState() => _SeriesDetailScreenState();
}

class _SeriesDetailScreenState extends State<SeriesDetailScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await widget.api.getSeriesDetail(widget.anchorId);
      if (mounted) setState(() { _data = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _markAllRead() async {
    final issues = (_data?['issues'] as List? ?? []).cast<Map<String, dynamic>>();
    for (final iss in issues) {
      await widget.api.markRead(iss['id'] as int);
    }
    _load();
  }

  Future<void> _toggleStatus(int issueId, String currentStatus) async {
    if (currentStatus == 'read') {
      await widget.api.markUnread(issueId);
    } else {
      await widget.api.markRead(issueId);
    }
    _load();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.redAccent)));
    }

    final d = _data!;
    final seriesName = d['series'] as String;
    final publisher = d['publisher'] as String?;
    final year = d['year'] as int?;
    final genres = List<String>.from(d['genres'] as List? ?? []);
    final coverPath = d['cover_path'] as String?;
    final issues = (d['issues'] as List).cast<Map<String, dynamic>>();
    final orientation = MediaQuery.orientationOf(context);
    final backdropHeight = orientation == Orientation.portrait ? 420.0 : 360.0;

    return Stack(
      children: [
        if (coverPath != null)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: backdropHeight,
            child: BlurredBackdrop(imageUrl: '${widget.api.baseUrl}$coverPath'),
          ),
        CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              sliver: SliverToBoxAdapter(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _AccentPill(label: '← Back', onTap: () => Navigator.of(context).pop()),
                        _AccentPill(label: 'Mark all read', onTap: _markAllRead),
                      ],
                    ),
                    const SizedBox(height: 18),
                    Text(seriesName, style: AppText.titleMedium()),
                    const SizedBox(height: 8),
                    Text(
                      [?publisher, ?year?.toString()].join(' · '),
                      style: AppText.secondary(),
                    ),
                    const SizedBox(height: 12),
                    if (genres.isNotEmpty)
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: genres.map((g) => _Tag(label: g)).toList(),
                      ),
                    const SizedBox(height: 12),
                    Text('${issues.length} issue${issues.length == 1 ? '' : 's'}', style: AppText.meta()),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
              sliver: SliverList.separated(
                itemCount: issues.length,
                separatorBuilder: (_, _) => const SizedBox(height: 8),
                itemBuilder: (context, i) {
                  final iss = issues[i];
                  return _IssueRow(
                    issue: iss,
                    api: widget.api,
                    downloads: widget.downloads,
                    seriesName: seriesName,
                    onToggleStatus: _toggleStatus,
                    onOpen: () => Navigator.of(context).pushNamed('/issue', arguments: iss['id'] as int),
                  );
                },
              ),
            ),
          ],
        ),
      ],
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

class _IssueRow extends StatefulWidget {
  final Map<String, dynamic> issue;
  final ApiService api;
  final DownloadService downloads;
  final String seriesName;
  final Future<void> Function(int issueId, String currentStatus) onToggleStatus;
  final VoidCallback onOpen;

  const _IssueRow({
    required this.issue,
    required this.api,
    required this.downloads,
    required this.seriesName,
    required this.onToggleStatus,
    required this.onOpen,
  });

  @override
  State<_IssueRow> createState() => _IssueRowState();
}

class _IssueRowState extends State<_IssueRow> {
  bool _downloading = false;

  @override
  Widget build(BuildContext context) {
    final issue = widget.issue;
    final number = issue['number'] as String?;
    final title = issue['title'] as String?;
    final year = issue['year'] as int?;
    final pageCount = issue['page_count'] as int?;
    final summary = issue['summary'] as String?;
    final readStatus = issue['read_status'] as String? ?? 'unread';
    final missing = issue['missing'] as bool? ?? false;
    final coverPath = issue['cover_path'] as String? ?? '';

    final borderColor = readStatus == 'read'
        ? AppColors.readGreen
        : (readStatus == 'reading' ? AppColors.accent : AppColors.border);
    final bgColor = readStatus == 'reading' ? AppColors.accent.withValues(alpha: 0.08) : AppColors.surfaceCard;

    // BoxDecoration.border rejects a borderRadius when side colors aren't
    // uniform, so the 3px status-colored left edge is layered separately
    // (a Positioned strip) rather than folded into the card's own border.
    return ClipRRect(
      borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                color: bgColor,
                border: Border.all(color: AppColors.border),
              ),
            ),
          ),
          Positioned(
            left: 0,
            top: 0,
            bottom: 0,
            width: 3,
            child: Container(color: borderColor),
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: GestureDetector(
              onTap: missing ? null : widget.onOpen,
              child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(AppSpacing.radiusXs),
              child: SizedBox(
                width: 56,
                height: 84,
                child: CachedNetworkImage(
                  imageUrl: '${widget.api.baseUrl}$coverPath',
                  fit: BoxFit.cover,
                  errorWidget: (_, _, _) => Container(color: AppColors.surfaceRaised, child: const Icon(Icons.menu_book_outlined, color: AppColors.textMuted)),
                ),
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 34,
              child: Text(
                number != null ? '#$number' : '',
                textAlign: TextAlign.center,
                style: AppText.label(size: 13, weight: FontWeight.w700, color: AppColors.textSecondary),
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title ?? widget.seriesName,
                    style: AppText.label(size: 14, color: missing ? AppColors.textMuted : AppColors.textPrimary),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    [if (year != null) '$year', if (pageCount != null) '$pageCount pages'].join(' · '),
                    style: AppText.meta(),
                  ),
                  if (summary != null && summary.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(summary, style: AppText.meta(), maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            if (!missing) _buildDownloadButton(),
            const SizedBox(width: 8),
            StatusButton(
              status: readStatus,
              onTap: () => widget.onToggleStatus(issue['id'] as int, readStatus),
            ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDownloadButton() {
    if (_downloading) {
      return const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2));
    }
    final id = widget.issue['id'] as int;
    final downloaded = widget.downloads.findByIssueId(id) != null;
    return IconButton(
      icon: Icon(
        downloaded ? Icons.download_done : Icons.download_for_offline_outlined,
        color: downloaded ? Colors.greenAccent : AppColors.textMuted,
        size: 20,
      ),
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
      constraints: const BoxConstraints(),
      onPressed: () => downloaded ? _confirmDelete(id) : _download(id),
    );
  }

  Future<void> _download(int id) async {
    setState(() => _downloading = true);
    try {
      await widget.downloads.download(
        id,
        series: widget.seriesName,
        number: widget.issue['number'] as String?,
        title: widget.issue['title'] as String?,
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Download failed: $e')));
      }
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _confirmDelete(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Remove download?'),
        content: const Text('This deletes the offline copy from this device.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Remove')),
        ],
      ),
    );
    if (confirmed == true) {
      await widget.downloads.delete(id);
      if (mounted) setState(() {});
    }
  }
}
