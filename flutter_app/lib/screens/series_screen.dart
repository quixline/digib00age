import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';
import '../services/download_service.dart';

class SeriesScreen extends StatefulWidget {
  final int anchorId;
  final ApiService api;
  final DownloadService downloads;

  const SeriesScreen({
    super.key,
    required this.anchorId,
    required this.api,
    required this.downloads,
  });

  @override
  State<SeriesScreen> createState() => _SeriesScreenState();
}

class _SeriesScreenState extends State<SeriesScreen> {
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

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(child: Text(_error!, style: const TextStyle(color: Colors.redAccent))),
      );
    }

    final d = _data!;
    final seriesName = d['series'] as String;
    final publisher = d['publisher'] as String?;
    final year = d['year'] as int?;
    final genres = List<String>.from(d['genres'] as List? ?? []);
    final coverPath = d['cover_path'] as String?;
    final issues = (d['issues'] as List).cast<Map<String, dynamic>>();

    // Group by story arc
    final arcGroups = <String?, List<Map<String, dynamic>>>{};
    for (final iss in issues) {
      final arc = iss['story_arc'] as String?;
      arcGroups.putIfAbsent(arc, () => []).add(iss);
    }

    final hasArcs = arcGroups.keys.any((k) => k != null && k.isNotEmpty);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(seriesName, style: const TextStyle(fontSize: 14)),
              background: coverPath != null
                  ? CachedNetworkImage(
                      imageUrl: '${widget.api.baseUrl}$coverPath',
                      fit: BoxFit.cover,
                      color: Colors.black45,
                      colorBlendMode: BlendMode.darken,
                    )
                  : null,
            ),
            actions: [
              TextButton.icon(
                onPressed: _markAllRead,
                icon: const Icon(Icons.done_all, color: Colors.white),
                label: const Text('Mark all read', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (publisher != null || year != null)
                    Text(
                      [?publisher, ?year?.toString()].join(' · '),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white60),
                    ),
                  if (genres.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      children: genres.map((g) => Chip(
                        label: Text(g, style: const TextStyle(fontSize: 11)),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                      )).toList(),
                    ),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    '${issues.length} issue${issues.length == 1 ? '' : 's'}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          if (hasArcs)
            _buildArcGroups(arcGroups, seriesName)
          else
            _buildFlatList(issues, seriesName),
        ],
      ),
    );
  }

  Widget _buildFlatList(List<Map<String, dynamic>> issues, String seriesName) {
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, i) => _IssueTile(
          issue: issues[i],
          api: widget.api,
          downloads: widget.downloads,
          seriesName: seriesName,
        ),
        childCount: issues.length,
      ),
    );
  }

  Widget _buildArcGroups(Map<String?, List<Map<String, dynamic>>> groups, String seriesName) {
    final noArc = groups[null] ?? [];
    final arcs = groups.entries
        .where((e) => e.key != null && e.key!.isNotEmpty)
        .toList()
      ..sort((a, b) {
        final aNum = (a.value.first['story_arc_number'] as int?) ?? 999;
        final bNum = (b.value.first['story_arc_number'] as int?) ?? 999;
        return aNum.compareTo(bNum);
      });

    final sections = <Widget>[];
    for (final entry in arcs) {
      sections.add(_ArcHeader(title: entry.key!));
      for (final iss in entry.value) {
        sections.add(_IssueTile(
          issue: iss,
          api: widget.api,
          downloads: widget.downloads,
          seriesName: seriesName,
        ));
      }
    }
    for (final iss in noArc) {
      sections.add(_IssueTile(
        issue: iss,
        api: widget.api,
        downloads: widget.downloads,
        seriesName: seriesName,
      ));
    }

    return SliverList(
      delegate: SliverChildListDelegate(sections),
    );
  }
}

class _ArcHeader extends StatelessWidget {
  final String title;
  const _ArcHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleSmall?.copyWith(
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }
}

class _IssueTile extends StatefulWidget {
  final Map<String, dynamic> issue;
  final ApiService api;
  final DownloadService downloads;
  final String seriesName;

  const _IssueTile({
    required this.issue,
    required this.api,
    required this.downloads,
    required this.seriesName,
  });

  @override
  State<_IssueTile> createState() => _IssueTileState();
}

class _IssueTileState extends State<_IssueTile> {
  bool _downloading = false;

  @override
  Widget build(BuildContext context) {
    final issue = widget.issue;
    final id = issue['id'] as int;
    final number = issue['number'] as String?;
    final title = issue['title'] as String?;
    final year = issue['year'] as int?;
    final readStatus = issue['read_status'] as String? ?? 'unread';
    final missing = issue['missing'] as bool? ?? false;
    final bw = issue['black_and_white'] as bool? ?? false;
    final coverPath = issue['cover_path'] as String? ?? '';

    final label = number != null ? '#$number' : (title ?? 'Issue');

    return ListTile(
      leading: SizedBox(
        width: 40,
        height: 56,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: CachedNetworkImage(
            imageUrl: '${widget.api.baseUrl}$coverPath',
            fit: BoxFit.cover,
            errorWidget: (_, _, _) =>
                const Icon(Icons.book, color: Colors.white24),
          ),
        ),
      ),
      title: Text(
        label,
        style: TextStyle(
          color: missing ? Colors.white38 : null,
          fontSize: 14,
        ),
      ),
      subtitle: Row(
        children: [
          if (year != null) Text('$year', style: const TextStyle(fontSize: 12)),
          if (bw) ...[
            const SizedBox(width: 6),
            const _Badge('B&W'),
          ],
          if (missing) ...[
            const SizedBox(width: 6),
            const _Badge('Missing', color: Colors.redAccent),
          ],
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (!missing) _buildDownloadButton(id, number, title),
          const SizedBox(width: 6),
          _statusIcon(readStatus),
        ],
      ),
      onTap: missing
          ? null
          : () => Navigator.of(context).pushNamed('/reader', arguments: id),
    );
  }

  Widget _buildDownloadButton(int id, String? number, String? title) {
    if (_downloading) {
      return const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }
    final downloaded = widget.downloads.findByIssueId(id) != null;
    return IconButton(
      icon: Icon(
        downloaded ? Icons.download_done : Icons.download_for_offline_outlined,
        color: downloaded ? Colors.greenAccent : Colors.white54,
        size: 20,
      ),
      visualDensity: VisualDensity.compact,
      padding: EdgeInsets.zero,
      constraints: const BoxConstraints(),
      onPressed: () => downloaded ? _confirmDelete(id) : _download(id, number, title),
    );
  }

  Future<void> _download(int id, String? number, String? title) async {
    setState(() => _downloading = true);
    try {
      await widget.downloads.download(
        id,
        series: widget.seriesName,
        number: number,
        title: title,
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Download failed: $e')),
        );
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

  Widget _statusIcon(String status) {
    switch (status) {
      case 'read':
        return const Icon(Icons.check_circle, color: Colors.greenAccent, size: 20);
      case 'reading':
        return const Icon(Icons.bookmark, color: Colors.orangeAccent, size: 20);
      default:
        return const Icon(Icons.radio_button_unchecked, color: Colors.white24, size: 20);
    }
  }
}

class _Badge extends StatelessWidget {
  final String label;
  final Color color;
  const _Badge(this.label, {this.color = Colors.white38});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
      decoration: BoxDecoration(
        border: Border.all(color: color, width: 0.8),
        borderRadius: BorderRadius.circular(3),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10)),
    );
  }
}
