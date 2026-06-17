import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';

// ── Tab widget — year grid ────────────────────────────────────────────────────

class TwoThousandAdTab extends StatefulWidget {
  final ApiService api;
  const TwoThousandAdTab({super.key, required this.api});

  @override
  State<TwoThousandAdTab> createState() => _TwoThousandAdTabState();
}

class _TwoThousandAdTabState extends State<TwoThousandAdTab>
    with AutomaticKeepAliveClientMixin {
  List<Map<String, dynamic>> _years = [];
  bool _loading = true;
  String? _error;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final years = await widget.api.get2000adYears();
      if (mounted) setState(() { _years = years; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);

    if (_loading) return const Center(child: CircularProgressIndicator());

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    }

    if (_years.isEmpty) {
      return const Center(
        child: Text('No 2000 AD progs found.', style: TextStyle(color: Colors.white38)),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: GridView.builder(
        padding: const EdgeInsets.all(8),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 160,
          childAspectRatio: 0.65,
          crossAxisSpacing: 8,
          mainAxisSpacing: 8,
        ),
        itemCount: _years.length,
        itemBuilder: (context, i) {
          final y = _years[i];
          return _YearCard(
            yearData: y,
            api: widget.api,
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => TwoThousandAdYearScreen(
                  year: y['year'] as int,
                  api: widget.api,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

// ── Year card (grid cell) ─────────────────────────────────────────────────────

class _YearCard extends StatelessWidget {
  final Map<String, dynamic> yearData;
  final ApiService api;
  final VoidCallback onTap;

  const _YearCard({
    required this.yearData,
    required this.api,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final year       = yearData['year'] as int;
    final coverPath  = yearData['cover_path'] as String?;
    final firstProg  = yearData['first_prog'] as int?;
    final lastProg   = yearData['last_prog'] as int?;
    final issueCount = yearData['issue_count'] as int? ?? 0;
    final range = (firstProg != null && lastProg != null)
        ? '#$firstProg–$lastProg'
        : '$issueCount progs';

    return GestureDetector(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: coverPath != null
                  ? CachedNetworkImage(
                      imageUrl: '${api.baseUrl}$coverPath',
                      fit: BoxFit.cover,
                      width: double.infinity,
                      errorWidget: (_, _, _) => _placeholder(),
                    )
                  : _placeholder(),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$year',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          Text(
            range,
            style: const TextStyle(fontSize: 10, color: Colors.white38),
          ),
        ],
      ),
    );
  }

  Widget _placeholder() => Container(
    color: Colors.white10,
    child: const Center(
      child: Icon(Icons.calendar_today, color: Colors.white24, size: 32),
    ),
  );
}

// ── Year detail screen ────────────────────────────────────────────────────────

class TwoThousandAdYearScreen extends StatefulWidget {
  final int year;
  final ApiService api;

  const TwoThousandAdYearScreen({
    super.key,
    required this.year,
    required this.api,
  });

  @override
  State<TwoThousandAdYearScreen> createState() => _TwoThousandAdYearScreenState();
}

class _TwoThousandAdYearScreenState extends State<TwoThousandAdYearScreen> {
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
      final data = await widget.api.get2000adYear(widget.year);
      if (mounted) setState(() { _data = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text('2000 AD · ${widget.year}')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: Text('2000 AD · ${widget.year}')),
        body: Center(
          child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
        ),
      );
    }

    final issues = (_data!['issues'] as List).cast<Map<String, dynamic>>();
    final backdropPath = issues.isNotEmpty ? issues.first['cover_path'] as String? : null;

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                '2000 AD · ${widget.year}',
                style: const TextStyle(fontSize: 14),
              ),
              background: backdropPath != null
                  ? CachedNetworkImage(
                      imageUrl: '${widget.api.baseUrl}$backdropPath',
                      fit: BoxFit.cover,
                      color: Colors.black45,
                      colorBlendMode: BlendMode.darken,
                    )
                  : null,
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
              child: Text(
                '${issues.length} issue${issues.length == 1 ? '' : 's'}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, i) => _ProgTile(issue: issues[i], api: widget.api),
              childCount: issues.length,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Prog tile ─────────────────────────────────────────────────────────────────

class _ProgTile extends StatelessWidget {
  final Map<String, dynamic> issue;
  final ApiService api;

  const _ProgTile({required this.issue, required this.api});

  @override
  Widget build(BuildContext context) {
    final id          = issue['id'] as int;
    final number      = issue['number'] as String?;
    final title       = issue['title'] as String?;
    final pageCount   = issue['page_count'] as int?;
    final readStatus  = issue['read_status'] as String? ?? 'unread';
    final missing     = issue['missing'] as bool? ?? false;
    final coverPath   = issue['cover_path'] as String? ?? '';
    final currentPage = issue['current_page'] as int? ?? 0;

    return ListTile(
      leading: SizedBox(
        width: 40,
        height: 56,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: CachedNetworkImage(
            imageUrl: '${api.baseUrl}$coverPath',
            fit: BoxFit.cover,
            errorWidget: (_, _, _) =>
                const Icon(Icons.book, color: Colors.white24),
          ),
        ),
      ),
      title: Text(
        number != null ? 'Prog #$number' : (title ?? 'Unknown'),
        style: TextStyle(
          color: missing ? Colors.white38 : null,
          fontSize: 14,
        ),
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null && title.isNotEmpty && number != null)
            Text(
              title,
              style: const TextStyle(fontSize: 12, color: Colors.white60),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          if (readStatus == 'reading' && pageCount != null && pageCount > 0)
            Text(
              'p.$currentPage / $pageCount',
              style: const TextStyle(fontSize: 11, color: Colors.orangeAccent),
            ),
        ],
      ),
      trailing: _statusIcon(readStatus),
      onTap: missing
          ? null
          : () => Navigator.of(context).pushNamed('/reader', arguments: id),
    );
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
