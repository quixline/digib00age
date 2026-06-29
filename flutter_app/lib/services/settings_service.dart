import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static const _keyServerUrl = 'server_url';
  static const _keyReadingMode = 'reading_mode';
  static const _keyConnectionMode = 'connection_mode';

  static const defaultServerUrl = 'http://192.168.1.10:9424';

  final SharedPreferences _prefs;

  SettingsService._(this._prefs);

  static Future<SettingsService> load() async {
    final prefs = await SharedPreferences.getInstance();
    return SettingsService._(prefs);
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
