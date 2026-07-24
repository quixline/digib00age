import 'package:flutter/material.dart';
import '../models/series.dart';
import '../services/api_service.dart';
import '../services/settings_service.dart';
import '../theme/tokens.dart';
import '../widgets/app_top_bar.dart';
import '../widgets/cover_card.dart';
import '../widgets/nav_rail.dart' show NavKind;
import '../widgets/page_backdrop.dart';
import '../widgets/pagination_bar.dart';

class BrowseFilter {
  final NavKind kind;
  final int? tabId;
  final String label; // eyebrow text, e.g. "All", "Unread", a library name
  final String? genre; // set when reached via an issue-page genre pill tap

  const BrowseFilter({required this.kind, this.tabId, required this.label, this.genre});
}

enum ViewMode { grid, list }

class BrowseScreen extends StatefulWidget {
  final ApiService api;
  final SettingsService settings;
  final BrowseFilter filter;
  final ViewMode viewMode;
  final ValueChanged<ViewMode> onViewModeChanged;
  final VoidCallback onSettingsReturn;

  const BrowseScreen({
    super.key,
    required this.api,
    required this.settings,
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
  int _currentPage = 1;

  @override
  void initState() {
    super.initState();
    _load();
    widget.settings.itemsPerPageNotifier.addListener(_onItemsPerPageChanged);
  }

  @override
  void dispose() {
    widget.settings.itemsPerPageNotifier.removeListener(_onItemsPerPageChanged);
    super.dispose();
  }

  // Settings is pushed on the root navigator, so this screen stays mounted
  // underneath — a page-size change needs to be picked up live rather than
  // waiting for a nav-rail reselection that would recreate this screen.
  void _onItemsPerPageChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final f = widget.filter;
      // Custom tabs are the only case that needs its own server-scoped fetch
      // (folder/favourites-scoped, not a subset of the same "All" pool).
      // Everything else fetches the full unfiltered library once and
      // filters client-side by each series' own format_group — mirroring
      // frontend/js/app.js's getFilteredLibrary() exactly. The backend's
      // `group=` query param filters at the ISSUE level before grouping by
      // series name, which fragments any series with mixed format_group
      // values across its issues (e.g. a Series-format run containing one
      // stray Singles-tagged special) into a phantom extra "singles" entry
      // that doesn't exist from the web's (correct) per-series-group point
      // of view — client-side filtering avoids that entirely.
      List<Series> list = f.kind == NavKind.library
          ? await widget.api.getLibrary(tabId: f.tabId)
          : await widget.api.getLibrary();
      switch (f.kind) {
        case NavKind.singles:
          list = list.where((s) => s.formatGroup == 'Singles').toList();
          break;
        case NavKind.series:
          list = list.where((s) => s.formatGroup == 'Series').toList();
          break;
        // Read-state filters mirror frontend/js/app.js:1073-1075 — applied
        // over the full "All" list, same principle as the web sidebar's
        // Unread/Reading/Read shortcuts.
        case NavKind.unread:
          list = list.where((s) => s.unreadCount == s.issueCount).toList();
          break;
        case NavKind.reading:
          list = list.where((s) => s.readingCount > 0).toList();
          break;
        case NavKind.read:
          list = list.where((s) => s.issueCount > 0 && s.readCount == s.issueCount).toList();
          break;
        case NavKind.all:
        case NavKind.library:
        case NavKind.home:
          break;
      }
      if (f.genre != null) {
        list = list.where((s) => s.genres.contains(f.genre)).toList();
      }
      if (!mounted) return;
      setState(() { _items = list; _loading = false; _currentPage = 1; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  // Mirrors frontend/js/app.js's isFlatSurface(): All, a custom library,
  // and the read-state shortcuts (which all operate on the All pool, just
  // pre-filtered) show the grand total of *individual comics* — series
  // count toward that total by their full issue_count, not as one card
  // each. Series/Singles show a plain card count instead.
  bool get _isFlatCount {
    switch (widget.filter.kind) {
      case NavKind.all:
      case NavKind.library:
      case NavKind.unread:
      case NavKind.reading:
      case NavKind.read:
        return true;
      case NavKind.series:
      case NavKind.singles:
      case NavKind.home:
        return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const Positioned.fill(child: PageBackdrop()),
        _buildContent(context),
      ],
    );
  }

  Widget _buildContent(BuildContext context) {
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
                    Text(widget.filter.label.toUpperCase(), style: AppText.of(context).eyebrow()),
                    const SizedBox(height: 2),
                    Text(_countLabel(), style: AppText.of(context).countBig()),
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
    final n = _isFlatCount
        ? _items.fold<int>(0, (sum, s) => sum + (s.issueCount > 0 ? s.issueCount : 1))
        : _items.length;
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

    final itemsPerPage = widget.settings.itemsPerPage;
    final totalPages = (_items.length / itemsPerPage).ceil().clamp(1, 1 << 30);
    _currentPage = _currentPage.clamp(1, totalPages);
    final start = (_currentPage - 1) * itemsPerPage;
    final pageItems = _items.sublist(start, (start + itemsPerPage).clamp(0, _items.length));

    return Column(
      children: [
        Expanded(
          child: RefreshIndicator(
            onRefresh: _load,
            child: widget.viewMode == ViewMode.grid ? _buildGrid(pageItems) : _buildList(pageItems),
          ),
        ),
        PaginationBar(
          currentPage: _currentPage,
          totalPages: totalPages,
          onPageChanged: (p) => setState(() => _currentPage = p),
        ),
      ],
    );
  }

  Widget _buildGrid(List<Series> items) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: AppSpacing.cardMin,
        childAspectRatio: 0.5,
        crossAxisSpacing: AppSpacing.cardGap,
        mainAxisSpacing: AppSpacing.cardGap,
      ),
      itemCount: items.length,
      itemBuilder: (context, i) => CoverCard(data: _cardFor(context, items[i])),
    );
  }

  Widget _buildList(List<Series> items) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
      itemCount: items.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, i) => CoverListRow(data: _cardFor(context, items[i])),
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
    final colors = AppColors.of(context);
    return Material(
      color: active ? colors.surfaceRaised : Colors.transparent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
        onTap: onTap,
        child: Container(
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            border: Border.all(color: colors.border),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
          ),
          child: Icon(icon, size: 18, color: active ? colors.textPrimary : colors.textMuted),
        ),
      ),
    );
  }
}
