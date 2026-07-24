import 'package:flutter/material.dart';
import '../models/custom_tab.dart';
import '../services/api_service.dart';
import '../services/settings_service.dart';
import '../services/local_cbz_service.dart';
import '../services/download_service.dart';
import '../services/sync_service.dart';
import '../route_observer.dart';
import '../theme/tokens.dart';
import '../widgets/nav_rail.dart';
import '../widgets/offline_library_view.dart';
import 'home_screen.dart';
import 'browse_screen.dart';
import 'series_detail_screen.dart';
import 'issue_detail_screen.dart';

class ShellScreen extends StatefulWidget {
  final ApiService api;
  final SettingsService settings;
  final LocalCbzService localCbz;
  final DownloadService downloads;
  final SyncService syncService;

  const ShellScreen({
    super.key,
    required this.api,
    required this.settings,
    required this.localCbz,
    required this.downloads,
    required this.syncService,
  });

  @override
  State<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends State<ShellScreen> with RouteAware {
  final _contentNavKey = GlobalKey<NavigatorState>();

  bool _serverOnline = false;
  bool _loading = true;
  bool? _collapsedOverride;
  NavTarget _active = homeTarget;
  List<CustomTabInfo> _customTabs = [];
  ViewMode _viewMode = ViewMode.grid;

  @override
  void initState() {
    super.initState();
    _checkAndLoad();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    routeObserver.subscribe(this, ModalRoute.of(context)! as PageRoute);
  }

  @override
  void dispose() {
    routeObserver.unsubscribe(this);
    super.dispose();
  }

  // Fires when a route pushed on top of this screen (reader, settings) is
  // popped back to it — mirrors the old LibraryScreen's use of RouteAware
  // (v2.5 Item 3): this screen is only pushed once at app start, so its own
  // initState() never re-runs on back-navigation.
  @override
  void didPopNext() => _checkAndLoad();

  Future<void> _checkAndLoad() async {
    final online = await widget.api.checkConnection();
    if (!mounted) return;
    setState(() => _serverOnline = online);
    if (!online) {
      setState(() => _loading = false);
      return;
    }
    try {
      final tabs = await widget.api.getNavConfig();
      if (mounted) setState(() { _customTabs = tabs; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
    widget.syncService.syncNow(); // best-effort, fire-and-forget
  }

  bool _railCollapsed(BuildContext context) {
    if (_collapsedOverride != null) return _collapsedOverride!;
    return MediaQuery.orientationOf(context) == Orientation.portrait;
  }

  void _onSelect(NavTarget target) {
    setState(() => _active = target);
    final route = _routeFor(target);
    _contentNavKey.currentState
        ?.pushNamedAndRemoveUntil(route.name, (_) => false, arguments: route.arguments);
  }

  ({String name, Object? arguments}) _routeFor(NavTarget target) {
    switch (target.kind) {
      case NavKind.home:
        return (name: '/home', arguments: null);
      case NavKind.all:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.all, label: 'All'));
      case NavKind.singles:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.singles, label: 'Singles'));
      case NavKind.series:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.series, label: 'Series'));
      case NavKind.unread:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.unread, label: 'Unread'));
      case NavKind.reading:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.reading, label: 'Reading'));
      case NavKind.read:
        return (name: '/browse', arguments: const BrowseFilter(kind: NavKind.read, label: 'Read'));
      case NavKind.library:
        final tab = _customTabs.firstWhere((t) => t.id == target.tabId);
        return (
          name: '/browse',
          arguments: BrowseFilter(kind: NavKind.library, tabId: tab.id, label: tab.name),
        );
    }
  }

  Route<dynamic>? _onGenerateRoute(RouteSettings routeSettings) {
    switch (routeSettings.name) {
      case '/home':
        return MaterialPageRoute(
          builder: (_) => HomeScreen(api: widget.api, onSettingsReturn: _checkAndLoad),
        );
      case '/browse':
        final filter = routeSettings.arguments as BrowseFilter;
        return MaterialPageRoute(
          builder: (_) => BrowseScreen(
            api: widget.api,
            settings: widget.settings,
            filter: filter,
            viewMode: _viewMode,
            onViewModeChanged: (m) => setState(() => _viewMode = m),
            onSettingsReturn: _checkAndLoad,
          ),
        );
      case '/series':
        final anchorId = routeSettings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => SeriesDetailScreen(anchorId: anchorId, api: widget.api, downloads: widget.downloads),
        );
      case '/issue':
        final issueId = routeSettings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => IssueDetailScreen(issueId: issueId, api: widget.api),
        );
      default:
        return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (!_serverOnline) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('ComicVault'),
          actions: [
            IconButton(
              icon: const Icon(Icons.settings),
              onPressed: () async {
                await Navigator.of(context).pushNamed('/settings');
                _checkAndLoad();
              },
            ),
          ],
        ),
        body: OfflineLibraryView(
          settings: widget.settings,
          localCbz: widget.localCbz,
          downloads: widget.downloads,
          syncService: widget.syncService,
          onRetry: _checkAndLoad,
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.of(context).canvas,
      body: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            NavRail(
              collapsed: _railCollapsed(context),
              active: _active,
              customTabs: _customTabs,
              onToggle: () => setState(() => _collapsedOverride = !_railCollapsed(context)),
              onSelect: _onSelect,
            ),
            Expanded(
              child: Navigator(
                key: _contentNavKey,
                initialRoute: '/home',
                onGenerateRoute: _onGenerateRoute,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
