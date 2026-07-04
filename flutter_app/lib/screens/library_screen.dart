import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/series.dart';
import '../services/api_service.dart';
import '../services/settings_service.dart';
import '../services/local_cbz_service.dart';

class LibraryScreen extends StatefulWidget {
  final ApiService api;
  final SettingsService settings;
  final LocalCbzService localCbz;

  const LibraryScreen({
    super.key,
    required this.api,
    required this.settings,
    required this.localCbz,
  });

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  bool _serverOnline = false;
  bool _loading = true;
  String? _error;

  List<Series> _seriesList = [];
  List<Series> _singlesList = [];
  List<Series> _allList = [];
  List<Map<String, dynamic>> _continueReading = [];

  String _searchQuery = '';
  String? _filterPublisher;
  String? _filterGenre;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _checkAndLoad();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _checkAndLoad() async {
    final online = await widget.api.checkConnection();
    if (!mounted) return;
    setState(() => _serverOnline = online);
    if (online) {
      await _loadLibrary();
    } else {
      setState(() => _loading = false);
    }
  }

  Future<void> _loadLibrary() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait([
        widget.api.getLibrary(group: 'Series'),
        widget.api.getLibrary(group: 'Singles'),
        widget.api.getLibrary(),
        widget.api.getContinueReading(),
      ]);
      if (!mounted) return;
      setState(() {
        _seriesList = results[0] as List<Series>;
        _singlesList = results[1] as List<Series>;
        _allList = results[2] as List<Series>;
        _continueReading = results[3] as List<Map<String, dynamic>>;
        _loading = false;
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<Series> _filtered(List<Series> list) {
    return list.where((s) {
      if (_searchQuery.isNotEmpty) {
        final q = _searchQuery.toLowerCase();
        if (!s.name.toLowerCase().contains(q) &&
            !(s.publisher?.toLowerCase().contains(q) ?? false)) {
          return false;
        }
      }
      if (_filterPublisher != null && s.publisher != _filterPublisher) return false;
      if (_filterGenre != null && !s.genres.contains(_filterGenre)) return false;
      return true;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ComicVault'),
        bottom: _serverOnline
            ? TabBar(
                controller: _tabs,
                tabs: const [
                  Tab(text: 'Series'),
                  Tab(text: 'Singles'),
                  Tab(text: 'All'),
                ],
              )
            : null,
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: _openSearch,
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () async {
              await Navigator.of(context).pushNamed('/settings');
              _checkAndLoad();
            },
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());

    if (!_serverOnline) return _buildOfflineBody();

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _loadLibrary, child: const Text('Retry')),
          ],
        ),
      );
    }

    return TabBarView(
      controller: _tabs,
      children: [
        _buildLibraryTab(_filtered(_seriesList), _seriesList),
        _buildLibraryTab(_filtered(_singlesList), _singlesList),
        _buildLibraryTab(_filtered(_allList), _allList),
      ],
    );
  }

  Widget _buildLibraryTab(List<Series> list, List<Series> full) {
    return RefreshIndicator(
      onRefresh: _loadLibrary,
      child: CustomScrollView(
        slivers: [
          // Search + filter bar
          SliverToBoxAdapter(child: _SearchFilterBar(
            query: _searchQuery,
            publisher: _filterPublisher,
            genre: _filterGenre,
            allPublishers: {
              for (final s in full) if (s.publisher != null) s.publisher!,
            }.toList()..sort(),
            allGenres: {
              for (final s in full) ...s.genres,
            }.toList()..sort(),
            onQueryChanged: (q) => setState(() => _searchQuery = q),
            onPublisherChanged: (p) => setState(() => _filterPublisher = p),
            onGenreChanged: (g) => setState(() => _filterGenre = g),
          )),
          // Continue reading strip
          if (_continueReading.isNotEmpty)
            SliverToBoxAdapter(
              child: _ContinueReadingStrip(
                items: _continueReading,
                api: widget.api,
              ),
            ),
          // Cover grid
          if (list.isEmpty)
            const SliverFillRemaining(
              child: Center(child: Text('No results', style: TextStyle(color: Colors.white38))),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.all(8),
              sliver: SliverGrid(
                gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                  maxCrossAxisExtent: 160,
                  childAspectRatio: 0.62,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 8,
                ),
                delegate: SliverChildBuilderDelegate(
                  (context, i) => _SeriesTile(series: list[i], api: widget.api),
                  childCount: list.length,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildOfflineBody() {
    final recentFiles = widget.settings.recentLocalFiles;
    return Column(
      children: [
        Container(
          width: double.infinity,
          color: Colors.orange.shade900,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              const Icon(Icons.wifi_off, size: 16),
              const SizedBox(width: 8),
              const Expanded(child: Text('Server offline — local files only', style: TextStyle(fontSize: 13))),
              TextButton(
                onPressed: _checkAndLoad,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: ElevatedButton.icon(
            onPressed: _openLocalFile,
            icon: const Icon(Icons.folder_open),
            label: const Text('Open local CBZ file'),
          ),
        ),
        if (recentFiles.isNotEmpty) ...[
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text('Recent files', style: TextStyle(color: Colors.white60)),
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: recentFiles.length,
              itemBuilder: (context, i) {
                final path = recentFiles[i];
                return ListTile(
                  leading: const Icon(Icons.book),
                  title: Text(widget.localCbz.titleFromPath(path), style: const TextStyle(fontSize: 14)),
                  subtitle: Text(path, style: const TextStyle(fontSize: 11, color: Colors.white38)),
                  onTap: () => Navigator.of(context).pushNamed(
                    '/reader/local',
                    arguments: path,
                  ),
                );
              },
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _openLocalFile() async {
    final path = await widget.localCbz.pickFile();
    if (path == null || !mounted) return;
    widget.settings.addRecentLocalFile(path);
    Navigator.of(context).pushNamed('/reader/local', arguments: path);
  }

  void _openSearch() async {
    await showSearch(
      context: context,
      delegate: _ComicSearchDelegate(api: widget.api),
    );
  }
}

// ---------------------------------------------------------------------------
// Search bar + filter row
// ---------------------------------------------------------------------------

class _SearchFilterBar extends StatefulWidget {
  final String query;
  final String? publisher;
  final String? genre;
  final List<String> allPublishers;
  final List<String> allGenres;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String?> onPublisherChanged;
  final ValueChanged<String?> onGenreChanged;

  const _SearchFilterBar({
    required this.query,
    required this.publisher,
    required this.genre,
    required this.allPublishers,
    required this.allGenres,
    required this.onQueryChanged,
    required this.onPublisherChanged,
    required this.onGenreChanged,
  });

  @override
  State<_SearchFilterBar> createState() => _SearchFilterBarState();
}

class _SearchFilterBarState extends State<_SearchFilterBar> {
  late TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.query);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _ctrl,
              decoration: InputDecoration(
                hintText: 'Search series…',
                prefixIcon: const Icon(Icons.search, size: 18),
                suffixIcon: _ctrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 18),
                        onPressed: () {
                          _ctrl.clear();
                          widget.onQueryChanged('');
                        },
                      )
                    : null,
                contentPadding: const EdgeInsets.symmetric(vertical: 8),
                isDense: true,
                border: const OutlineInputBorder(),
              ),
              onChanged: widget.onQueryChanged,
            ),
          ),
          const SizedBox(width: 8),
          _FilterButton(
            icon: Icons.business,
            value: widget.publisher,
            options: widget.allPublishers,
            onChanged: widget.onPublisherChanged,
          ),
          const SizedBox(width: 4),
          _FilterButton(
            icon: Icons.label,
            value: widget.genre,
            options: widget.allGenres,
            onChanged: widget.onGenreChanged,
          ),
        ],
      ),
    );
  }
}

class _FilterButton extends StatelessWidget {
  final IconData icon;
  final String? value;
  final List<String> options;
  final ValueChanged<String?> onChanged;

  const _FilterButton({
    required this.icon,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(icon, color: value != null ? Theme.of(context).colorScheme.primary : null),
      onPressed: () async {
        final chosen = await showDialog<String?>(
          context: context,
          builder: (_) => _FilterDialog(options: options, current: value),
        );
        if (chosen != null) onChanged(chosen.isEmpty ? null : chosen);
      },
    );
  }
}

class _FilterDialog extends StatelessWidget {
  final List<String> options;
  final String? current;
  const _FilterDialog({required this.options, this.current});

  @override
  Widget build(BuildContext context) {
    return SimpleDialog(
      children: [
        SimpleDialogOption(
          onPressed: () => Navigator.pop(context, ''),
          child: const Text('(All)'),
        ),
        for (final opt in options)
          SimpleDialogOption(
            onPressed: () => Navigator.pop(context, opt),
            child: Text(
              opt,
              style: TextStyle(
                fontWeight: opt == current ? FontWeight.bold : null,
              ),
            ),
          ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Continue reading strip
// ---------------------------------------------------------------------------

class _ContinueReadingStrip extends StatelessWidget {
  final List<Map<String, dynamic>> items;
  final ApiService api;

  const _ContinueReadingStrip({required this.items, required this.api});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(12, 12, 12, 6),
          child: Text(
            'Continue Reading',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
          ),
        ),
        SizedBox(
          height: 120,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: items.length,
            itemBuilder: (context, i) {
              final item = items[i];
              final id = item['id'] as int;
              final series = item['series'] as String;
              final number = item['number'] as String?;
              final coverPath = item['cover_path'] as String? ?? '';
              final currentPage = item['current_page'] as int? ?? 0;
              final pageCount = item['page_count'] as int? ?? 1;
              final progress = currentPage / pageCount.clamp(1, 99999);

              return GestureDetector(
                onTap: () => Navigator.of(context).pushNamed('/reader', arguments: id),
                child: Container(
                  width: 76,
                  margin: const EdgeInsets.only(right: 8),
                  child: Column(
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: Stack(
                            children: [
                              CachedNetworkImage(
                                imageUrl: '${api.baseUrl}$coverPath',
                                fit: BoxFit.cover,
                                width: 76,
                                height: double.infinity,
                                errorWidget: (_, _, _) =>
                                    const Icon(Icons.book, color: Colors.white24),
                              ),
                              Positioned(
                                bottom: 0,
                                left: 0,
                                right: 0,
                                child: LinearProgressIndicator(
                                  value: progress,
                                  minHeight: 3,
                                  backgroundColor: Colors.black38,
                                  color: Colors.orangeAccent,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        number != null ? '$series #$number' : series,
                        style: const TextStyle(fontSize: 10),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Series tile (grid cell)
// ---------------------------------------------------------------------------

class _SeriesTile extends StatelessWidget {
  final Series series;
  final ApiService api;

  const _SeriesTile({required this.series, required this.api});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.of(context)
          .pushNamed('/series', arguments: series.seriesAnchorId),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  CachedNetworkImage(
                    imageUrl: '${api.baseUrl}${series.coverPath}',
                    fit: BoxFit.cover,
                    errorWidget: (_, _, _) => Container(
                      color: Colors.white10,
                      child: const Icon(Icons.book, color: Colors.white24, size: 40),
                    ),
                  ),
                  if (series.unreadCount > 0)
                    Positioned(
                      top: 4,
                      right: 4,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primary,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '${series.unreadCount}',
                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            series.name,
            style: const TextStyle(fontSize: 11),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (series.publisher != null)
            Text(
              series.publisher!,
              style: const TextStyle(fontSize: 10, color: Colors.white38),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Search delegate
// ---------------------------------------------------------------------------

class _ComicSearchDelegate extends SearchDelegate<void> {
  final ApiService api;
  _ComicSearchDelegate({required this.api});

  @override
  List<Widget> buildActions(BuildContext context) => [
    IconButton(icon: const Icon(Icons.clear), onPressed: () => query = ''),
  ];

  @override
  Widget buildLeading(BuildContext context) =>
      IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => close(context, null));

  @override
  Widget buildResults(BuildContext context) => _buildResultList(context);

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.length < 2) {
      return const Center(child: Text('Type at least 2 characters…', style: TextStyle(color: Colors.white38)));
    }
    return _buildResultList(context);
  }

  Widget _buildResultList(BuildContext context) {
    if (query.length < 2) return const SizedBox.shrink();
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: api.search(query),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text(snap.error.toString(), style: const TextStyle(color: Colors.redAccent)));
        }
        final results = snap.data ?? [];
        if (results.isEmpty) {
          return const Center(child: Text('No results', style: TextStyle(color: Colors.white38)));
        }
        return ListView.builder(
          itemCount: results.length,
          itemBuilder: (context, i) {
            final r = results[i];
            final id = r['id'] as int;
            final series = r['series'] as String;
            final number = r['number'] as String?;
            final coverPath = r['cover_path'] as String? ?? '';
            return ListTile(
              leading: SizedBox(
                width: 32,
                height: 44,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(2),
                  child: CachedNetworkImage(
                    imageUrl: '${api.baseUrl}$coverPath',
                    fit: BoxFit.cover,
                    errorWidget: (_, _, _) => const Icon(Icons.book, size: 20),
                  ),
                ),
              ),
              title: Text(series, style: const TextStyle(fontSize: 14)),
              subtitle: number != null ? Text('#$number') : null,
              onTap: () {
                close(context, null);
                Navigator.of(context).pushNamed('/reader', arguments: id);
              },
            );
          },
        );
      },
    );
  }
}
