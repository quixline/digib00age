import 'package:flutter/material.dart';
import '../models/series.dart';
import '../services/api_service.dart';
import '../theme/tokens.dart';
import '../widgets/app_top_bar.dart';
import '../widgets/cover_card.dart';
import '../widgets/nav_rail.dart' show NavKind;

class BrowseFilter {
  final NavKind kind;
  final int? tabId;
  final String label; // eyebrow text, e.g. "All", "Unread", a library name

  const BrowseFilter({required this.kind, this.tabId, required this.label});
}

enum ViewMode { grid, list }

class BrowseScreen extends StatefulWidget {
  final ApiService api;
  final BrowseFilter filter;
  final ViewMode viewMode;
  final ValueChanged<ViewMode> onViewModeChanged;
  final VoidCallback onSettingsReturn;

  const BrowseScreen({
    super.key,
    required this.api,
    required this.filter,
    required this.viewMode,
    required this.onViewModeChanged,
    required this.onSettingsReturn,
  });

  @override
  State<BrowseScreen> createState() => _BrowseScreenState();
}

class _BrowseScreenState extends State<BrowseScreen> {
  List<Series> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final f = widget.filter;
      List<Series> list;
      switch (f.kind) {
        case NavKind.singles:
          list = await widget.api.getLibrary(group: 'Singles');
          break;
        case NavKind.series:
          list = await widget.api.getLibrary(group: 'Series');
          break;
        case NavKind.library:
          list = await widget.api.getLibrary(tabId: f.tabId);
          break;
        case NavKind.unread:
        case NavKind.reading:
        case NavKind.read:
        case NavKind.all:
        case NavKind.home:
          list = await widget.api.getLibrary();
      }
      // Read-state filters mirror frontend/js/app.js:1073-1075 — applied
      // over the full "All" list, same principle as the web sidebar's
      // Unread/Reading/Read shortcuts.
      switch (f.kind) {
        case NavKind.unread:
          list = list.where((s) => s.unreadCount == s.issueCount).toList();
          break;
        case NavKind.reading:
          list = list.where((s) => s.readingCount > 0).toList();
          break;
        case NavKind.read:
          list = list.where((s) => s.issueCount > 0 && s.readCount == s.issueCount).toList();
          break;
        default:
          break;
      }
      if (!mounted) return;
      setState(() { _items = list; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppTopBar(api: widget.api, onSettingsReturn: widget.onSettingsReturn),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.filter.label.toUpperCase(), style: AppText.eyebrow()),
                    const SizedBox(height: 2),
                    Text(_countLabel(), style: AppText.countBig()),
                  ],
                ),
              ),
              _ViewToggleButton(
                icon: Icons.grid_view,
                active: widget.viewMode == ViewMode.grid,
                onTap: () => widget.onViewModeChanged(ViewMode.grid),
              ),
              const SizedBox(width: 8),
              _ViewToggleButton(
                icon: Icons.view_list,
                active: widget.viewMode == ViewMode.list,
                onTap: () => widget.onViewModeChanged(ViewMode.list),
              ),
            ],
          ),
        ),
        Expanded(child: _buildBody()),
      ],
    );
  }

  String _countLabel() {
    final n = _items.length;
    final str = n.toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (m) => ',',
    );
    return '$str Title${n == 1 ? '' : 's'}';
  }

  Widget _buildBody() {
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
    if (_items.isEmpty) {
      return const Center(child: Text('No results', style: TextStyle(color: Colors.white38)));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: widget.viewMode == ViewMode.grid ? _buildGrid() : _buildList(),
    );
  }

  Widget _buildGrid() {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: AppSpacing.cardMin,
        childAspectRatio: 0.5,
        crossAxisSpacing: AppSpacing.cardGap,
        mainAxisSpacing: AppSpacing.cardGap,
      ),
      itemCount: _items.length,
      itemBuilder: (context, i) => CoverCard(data: _cardFor(context, _items[i])),
    );
  }

  Widget _buildList() {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
      itemCount: _items.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, i) => CoverListRow(data: _cardFor(context, _items[i])),
    );
  }

  CoverCardData _cardFor(BuildContext context, Series s) {
    final isSingle = s.formatGroup == 'Singles';
    final meta = isSingle
        ? [if (s.year != null) '${s.year}', if (s.pageCount != null) '${s.pageCount} pages'].join(' · ')
        : [if (s.year != null) '${s.year}', '${s.issueCount} issues'].join(' · ');
    final credLabel = [
      if (s.publisher != null) s.publisher!,
      if (s.writers.isNotEmpty) s.writers.first,
    ].join(' · ');

    return CoverCardData(
      title: s.name,
      meta: meta,
      coverUrl: '${widget.api.baseUrl}${s.coverPath}',
      state: s.readState,
      progressPercent: s.progressPercent,
      favourite: s.favorites,
      unreadCount: isSingle ? 0 : s.unreadCount,
      summary: s.summary,
      genresLabel: s.genres.join(' · '),
      credLabel: credLabel,
      onTap: () {
        if (isSingle) {
          Navigator.of(context).pushNamed('/issue', arguments: s.seriesAnchorId);
        } else {
          Navigator.of(context).pushNamed('/series', arguments: s.seriesAnchorId);
        }
      },
    );
  }
}

class _ViewToggleButton extends StatelessWidget {
  final IconData icon;
  final bool active;
  final VoidCallback onTap;

  const _ViewToggleButton({required this.icon, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: active ? AppColors.surfaceRaised : Colors.transparent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
        onTap: onTap,
        child: Container(
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
          ),
          child: Icon(icon, size: 18, color: active ? AppColors.textPrimary : AppColors.textMuted),
        ),
      ),
    );
  }
}
