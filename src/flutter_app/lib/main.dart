import 'package:flutter/material.dart';
import 'package:app_links/app_links.dart';
import 'services/api_service.dart';
import 'services/settings_service.dart';
import 'services/local_cbz_service.dart';
import 'services/download_service.dart';
import 'services/sync_store.dart';
import 'services/sync_service.dart';
import 'route_observer.dart';
import 'theme/tokens.dart';
import 'screens/shell_screen.dart';
import 'screens/reader_screen.dart';
import 'screens/settings_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final settings = await SettingsService.load();
  runApp(Digib00ageApp(settings: settings));
}

class Digib00ageApp extends StatefulWidget {
  final SettingsService settings;
  const Digib00ageApp({super.key, required this.settings});

  @override
  State<Digib00ageApp> createState() => _Digib00ageAppState();
}

class _Digib00ageAppState extends State<Digib00ageApp> {
  late final ApiService _api;
  late final LocalCbzService _localCbz;
  late final DownloadService _downloads;
  late final SyncStore _syncStore;
  late final SyncService _syncService;
  final _navigatorKey = GlobalKey<NavigatorState>();
  late final AppLinks _appLinks;

  @override
  void initState() {
    super.initState();
    _api = ApiService(widget.settings.serverUrl);
    _localCbz = LocalCbzService();
    _downloads = DownloadService(_api, widget.settings, _localCbz);
    _syncStore = SyncStore(widget.settings.prefs);
    _syncService = SyncService(_api, _syncStore, widget.settings);
    _initDeepLinks();
  }

  Future<void> _initDeepLinks() async {
    _appLinks = AppLinks();
    // Handle cold-start deep link
    final initial = await _appLinks.getInitialLink();
    if (initial != null) _handleLink(initial);
    // Handle links while app is running
    _appLinks.uriLinkStream.listen(_handleLink);
  }

  void _handleLink(Uri uri) {
    // digib00age://read/{issue_id}
    if (uri.scheme == 'digib00age' && uri.host == 'read') {
      final idStr = uri.pathSegments.isNotEmpty ? uri.pathSegments.first : null;
      final id = int.tryParse(idStr ?? '');
      if (id != null) {
        _navigatorKey.currentState?.pushNamed('/reader', arguments: id);
      }
      return;
    }
    // BUG-017: a .cbz opened from outside the app (file manager "Open
    // With", browser download) arrives here as a content://|file:// URI,
    // via the same app_links stream the digib00age:// deep link uses.
    if (uri.scheme == 'content' || uri.scheme == 'file') {
      _openSharedCbz(uri);
    }
  }

  Future<void> _openSharedCbz(Uri uri) async {
    try {
      final path = await _localCbz.resolveSharedUri(uri.toString());
      if (path == null) return;
      widget.settings.addRecentLocalFile(path);
      _navigatorKey.currentState?.pushNamed('/reader/local', arguments: LocalReaderArgs(path));
    } catch (_) {
      // Resolution failed (revoked permission, unreadable stream, etc.) —
      // nothing to open; fail silently rather than crash, same as
      // LibraryScreen._openLocalFile() does when the picker returns null.
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: widget.settings.themeModeNotifier,
      builder: (context, themeMode, _) => MaterialApp(
        title: 'digib00age',
        navigatorKey: _navigatorKey,
        navigatorObservers: [routeObserver],
        debugShowCheckedModeBanner: false,
        theme: buildLightTheme(),
        darkTheme: buildDarkTheme(),
        themeMode: themeMode,
        initialRoute: '/',
        onGenerateRoute: _buildRoute,
      ),
    );
  }

  Route<dynamic>? _buildRoute(RouteSettings routeSettings) {
    switch (routeSettings.name) {
      case '/':
        return MaterialPageRoute(
          builder: (_) => ShellScreen(
            api: _api,
            settings: widget.settings,
            localCbz: _localCbz,
            downloads: _downloads,
            syncService: _syncService,
          ),
        );
      case '/reader':
        final issueId = routeSettings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => ReaderScreen(
            issueId: issueId,
            api: _api,
            settings: widget.settings,
          ),
        );
      case '/reader/local':
        final args = routeSettings.arguments as LocalReaderArgs;
        return MaterialPageRoute(
          builder: (_) => LocalReaderScreen(
            filePath: args.filePath,
            settings: widget.settings,
            localCbz: _localCbz,
            issueId: args.issueId,
            syncStore: args.issueId != null ? _syncStore : null,
          ),
        );
      case '/settings':
        return MaterialPageRoute(
          builder: (_) => SettingsScreen(
            settings: widget.settings,
            api: _api,
          ),
        );
      default:
        return null;
    }
  }
}
