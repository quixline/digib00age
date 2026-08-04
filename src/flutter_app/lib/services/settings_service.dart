import 'package:flutter/material.dart' show ThemeMode, ValueNotifier;
import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static const _keyServerUrl = 'server_url';
  static const _keyReadingMode = 'reading_mode';
  static const _keyConnectionMode = 'connection_mode';
  static const _keyThemeMode = 'theme_mode';
  static const _keyItemsPerPage = 'items_per_page';

  static const defaultServerUrl = 'http://192.168.1.10:9800';
  static const _validItemsPerPage = {25, 50, 75, 100};

  final SharedPreferences _prefs;
  late final ValueNotifier<ThemeMode> themeModeNotifier;
  late final ValueNotifier<int> itemsPerPageNotifier;

  SettingsService._(this._prefs) {
    themeModeNotifier = ValueNotifier(_readThemeMode());
    itemsPerPageNotifier = ValueNotifier(_readItemsPerPage());
  }

  // Exposed so sibling services (DownloadService, SyncStore, SyncService)
  // can share the same storage instead of each opening their own.
  SharedPreferences get prefs => _prefs;

  static Future<SettingsService> load() async {
    final prefs = await SharedPreferences.getInstance();
    return SettingsService._(prefs);
  }

  ThemeMode _readThemeMode() {
    switch (_prefs.getString(_keyThemeMode)) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }

  // "auto" (follows OS) / "light" / "dark" — mirrors the web app's Admin
  // Appearance setting (frontend/js/admin.js initTheme()).
  ThemeMode get themeMode => themeModeNotifier.value;
  set themeMode(ThemeMode mode) {
    final raw = switch (mode) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'auto',
    };
    _prefs.setString(_keyThemeMode, raw);
    themeModeNotifier.value = mode;
  }

  String get serverUrl {
    final raw = _prefs.getString(_keyServerUrl) ?? defaultServerUrl;
    return _normalise(raw);
  }

  set serverUrl(String v) => _prefs.setString(_keyServerUrl, _normalise(v));

  static String _normalise(String url) {
    final trimmed = url.trim().replaceAll(RegExp(r'/+$'), '');
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }
    return 'http://$trimmed';
  }

  // "scroll" or "page"
  String get readingMode => _prefs.getString(_keyReadingMode) ?? 'scroll';
  set readingMode(String v) => _prefs.setString(_keyReadingMode, v);

  // Titles-per-page for library/custom-library browse pages — mirrors the
  // web app's Admin "Results per page" setting (frontend/js/admin.js
  // initPagination()), but with a phone-appropriate range.
  int _readItemsPerPage() {
    final raw = _prefs.getInt(_keyItemsPerPage) ?? 25;
    return _validItemsPerPage.contains(raw) ? raw : 25;
  }

  int get itemsPerPage => itemsPerPageNotifier.value;
  set itemsPerPage(int v) {
    final safe = _validItemsPerPage.contains(v) ? v : 25;
    _prefs.setInt(_keyItemsPerPage, safe);
    itemsPerPageNotifier.value = safe;
  }

  // "auto", "server", "local"
  String get connectionMode => _prefs.getString(_keyConnectionMode) ?? 'auto';
  set connectionMode(String v) => _prefs.setString(_keyConnectionMode, v);

  // Local progress for travel/offline mode — keyed by file path
  String _progressKey(String filePath) => 'local_progress:$filePath';

  void saveLocalProgress(String filePath, int currentPage, int totalPages) {
    _prefs.setString(_progressKey(filePath), '$currentPage/$totalPages');
  }

  ({int currentPage, int totalPages})? getLocalProgress(String filePath) {
    final raw = _prefs.getString(_progressKey(filePath));
    if (raw == null) return null;
    final parts = raw.split('/');
    if (parts.length != 2) return null;
    final page = int.tryParse(parts[0]);
    final total = int.tryParse(parts[1]);
    if (page == null || total == null) return null;
    return (currentPage: page, totalPages: total);
  }

  // Recently opened local files (file paths)
  List<String> get recentLocalFiles =>
      _prefs.getStringList('recent_local_files') ?? [];

  void addRecentLocalFile(String path) {
    final list = recentLocalFiles.toList();
    list.remove(path);
    list.insert(0, path);
    _prefs.setStringList('recent_local_files', list.take(10).toList());
  }
}
