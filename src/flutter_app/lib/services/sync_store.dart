import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

// Per-issue pending-sync record for a downloaded, offline-read comic.
// Dirty (needs pushing to the server) whenever updatedAt is newer than
// syncedAt (or syncedAt is null, meaning never synced).
class PendingProgress {
  final int issueId;
  int currentPage;
  String status;
  DateTime updatedAt;
  DateTime? syncedAt;

  PendingProgress({
    required this.issueId,
    required this.currentPage,
    required this.status,
    required this.updatedAt,
    this.syncedAt,
  });

  bool get isDirty => syncedAt == null || updatedAt.isAfter(syncedAt!);

  Map<String, dynamic> toJson() => {
        'issueId': issueId,
        'currentPage': currentPage,
        'status': status,
        'updatedAt': updatedAt.toIso8601String(),
        'syncedAt': syncedAt?.toIso8601String(),
      };

  factory PendingProgress.fromJson(Map<String, dynamic> j) => PendingProgress(
        issueId: j['issueId'] as int,
        currentPage: j['currentPage'] as int,
        status: j['status'] as String,
        updatedAt: DateTime.parse(j['updatedAt'] as String),
        syncedAt: j['syncedAt'] != null ? DateTime.parse(j['syncedAt'] as String) : null,
      );
}

class SyncStore {
  final SharedPreferences _prefs;
  SyncStore(this._prefs);

  static const _key = 'pending_progress';

  Map<int, PendingProgress> _load() {
    final raw = _prefs.getStringList(_key) ?? [];
    final list = raw.map((s) => PendingProgress.fromJson(jsonDecode(s) as Map<String, dynamic>));
    return {for (final p in list) p.issueId: p};
  }

  void _saveAll(Map<int, PendingProgress> map) {
    _prefs.setStringList(_key, map.values.map((p) => jsonEncode(p.toJson())).toList());
  }

  // Called on every page turn / status change for a DOWNLOADED issue only
  // (LocalReaderScreen only calls this when issueId != null). Always
  // captures the current moment in UTC — see backend/routers/sync.py's
  // _parse_client_ts docstring for why local time here would silently
  // corrupt the last-write-wins comparison.
  void recordProgress(int issueId, {required int currentPage, required String status}) {
    final map = _load();
    map[issueId] = PendingProgress(
      issueId: issueId,
      currentPage: currentPage,
      status: status,
      updatedAt: DateTime.now().toUtc(),
      syncedAt: map[issueId]?.syncedAt,
    );
    _saveAll(map);
  }

  List<PendingProgress> dirtyItems() => _load().values.where((p) => p.isDirty).toList();

  void markSynced(int issueId, {required DateTime syncedAt, int? serverPage, String? serverStatus}) {
    final map = _load();
    final existing = map[issueId];
    if (existing == null) return;
    map[issueId] = PendingProgress(
      issueId: issueId,
      currentPage: serverPage ?? existing.currentPage,
      status: serverStatus ?? existing.status,
      updatedAt: existing.updatedAt,
      syncedAt: syncedAt,
    );
    _saveAll(map);
  }
}
