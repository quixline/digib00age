import 'package:flutter/material.dart';
import 'package:app_links/app_links.dart';
import 'services/api_service.dart';
import 'services/settings_service.dart';
import 'services/local_cbz_service.dart';
import 'screens/library_screen.dart';
import 'screens/series_screen.dart';
import 'screens/reader_screen.dart';
import 'screens/settings_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final settings = await SettingsService.load();
  runApp(ComicVaultApp(settings: settings));
}

class ComicVaultApp extends StatefulWidget {
  final SettingsService settings;
  const ComicVaultApp({super.key, required this.settings});

  @override
  State<ComicVaultApp> createState() => _ComicVaultAppState();
}

class _ComicVaultAppState extends State<ComicVaultApp> {
  late final ApiService _api;
  late final LocalCbzService _localCbz;
  final _navigatorKey = GlobalKey<NavigatorState>();
  late final AppLinks _appLinks;

  @override
  void initState() {
    super.initState();
    _api = ApiService(widget.settings.serverUrl);
    _localCbz = LocalCbzService();
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
    // comicvault://read/{issue_id}
    if (uri.scheme == 'comicvault' && uri.host == 'read') {
      final idStr = uri.pathSegments.isNotEmpty ? uri.pathSegments.first : null;
      final id = int.tryParse(idStr ?? '');
      if (id != null) {
        _navigatorKey.currentState?.pushNamed('/reader', arguments: id);
      }
      return;
    }
    // BUG-017: a .cbz opened from outside the app (file manager "Open
    // With", browser download) arrives here as a content://|file:// URI,
    // via the same app_links stream the comicvault:// deep link uses.
    if (uri.scheme == 'content' || uri.scheme == 'file') {
      _openSharedCbz(uri);
    }
  }

  Future<void> _openSharedCbz(Uri uri) async {
    try {
      final path = await _localCbz.resolveSharedUri(uri.toString());
      if (path == null) return;
      widget.settings.addRecentLocalFile(path);
      _navigatorKey.currentState?.pushNamed('/reader/local', arguments: path);
    } catch (_) {
      // Resolution failed (revoked permission, unreadable stream, etc.) —
      // nothing to open; fail silently rather than crash, same as
      // LibraryScreen._openLocalFile() does when the picker returns null.
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ComicVault',
      navigatorKey: _navigatorKey,
      debugShowCheckedModeBanner: false,
      theme: _buildTheme(),
      initialRoute: '/',
      onGenerateRoute: _buildRoute,
    );
  }

  Route<dynamic>? _buildRoute(RouteSettings routeSettings) {
    switch (routeSettings.name) {
      case '/':
        return MaterialPageRoute(
          builder: (_) => LibraryScreen(
            api: _api,
            settings: widget.settings,
            localCbz: _localCbz,
          ),
        );
      case '/series':
        final anchorId = routeSettings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => SeriesScreen(anchorId: anchorId, api: _api),
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
        final filePath = routeSettings.arguments as String;
        return MaterialPageRoute(
          builder: (_) => LocalReaderScreen(
            filePath: filePath,
            settings: widget.settings,
            localCbz: _localCbz,
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

  ThemeData _buildTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.deepOrange,
        brightness: Brightness.dark,
      ),
      scaffoldBackgroundColor: const Color(0xFF111111),
      cardColor: const Color(0xFF1E1E1E),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF1A1A1A),
        elevation: 0,
        centerTitle: false,
      ),
      tabBarTheme: const TabBarThemeData(
        dividerColor: Colors.transparent,
      ),
    );
  }
}
