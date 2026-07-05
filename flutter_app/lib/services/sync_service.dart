import 'api_service.dart';
import 'settings_service.dart';
import 'sync_store.dart';

class SyncResult {
  final int pushed;
  final int serverWon;
  final int failed;
  SyncResult({required this.pushed, required this.serverWon, required this.failed});

  bool get hadWork => pushed + serverWon + failed > 0;
}

// Pushes locally-recorded offline reading progress to the server and
// reconciles the result (v2.5 Item 3). This only ever operates on issues
// read via a downloaded copy (SyncStore); ReaderScreen's online-mode reading
// already pushes progress directly and never touches this service.
class SyncService {
  final ApiService api;
  final SyncStore store;
  final SettingsService settings;

  SyncService(this.api, this.store, this.settings);

  static const _lastSyncedKey = 'last_synced_at';

  DateTime? get lastSyncedAt {
    final raw = settings.prefs.getString(_lastSyncedKey);
    return raw != null ? DateTime.parse(raw) : null;
  }

  Future<SyncResult> syncNow() async {
    final dirty = store.dirtyItems();
    if (dirty.isEmpty) {
      settings.prefs.setString(_lastSyncedKey, DateTime.now().toUtc().toIso8601String());
      return SyncResult(pushed: 0, serverWon: 0, failed: 0);
    }

    final payload = {
      'items': dirty
          .map((p) => {
                'issue_id': p.issueId,
                'current_page': p.currentPage,
                'status': p.status,
                'updated_at': p.updatedAt.toIso8601String(),
              })
          .toList(),
    };

    Map<String, dynamic> response;
    try {
      response = await api.syncProgress(payload);
    } catch (_) {
      // Network/server failure — everything stays dirty, retried next trigger.
      return SyncResult(pushed: 0, serverWon: 0, failed: dirty.length);
    }

    final now = DateTime.now().toUtc();
    int applied = 0, serverWon = 0, skipped = 0;
    for (final r in (response['results'] as List).cast<Map<String, dynamic>>()) {
      final issueId = r['issue_id'] as int;
      final outcome = r['outcome'] as String;
      if (outcome == 'not_found') {
        skipped++;
        continue;
      }
      store.markSynced(
        issueId,
        syncedAt: now,
        serverPage: r['current_page'] as int?,
        serverStatus: r['status'] as String?,
      );
      if (outcome == 'server_kept') {
        serverWon++;
      } else {
        applied++;
      }
    }
    settings.prefs.setString(_lastSyncedKey, now.toIso8601String());
    return SyncResult(pushed: applied, serverWon: serverWon, failed: skipped);
  }
}
