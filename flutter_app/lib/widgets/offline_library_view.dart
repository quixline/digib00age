// Shown by ShellScreen in place of the rail UI when the server is
// unreachable — rail navigation depends on live nav-config/library data that
// isn't available offline. Extracted from the old LibraryScreen unchanged.
import 'package:flutter/material.dart';
import '../services/settings_service.dart';
import '../services/local_cbz_service.dart';
import '../services/download_service.dart';
import '../services/sync_service.dart';
import '../screens/reader_screen.dart' show LocalReaderArgs;

class OfflineLibraryView extends StatelessWidget {
  final SettingsService settings;
  final LocalCbzService localCbz;
  final DownloadService downloads;
  final SyncService syncService;
  final VoidCallback onRetry;

  const OfflineLibraryView({
    super.key,
    required this.settings,
    required this.localCbz,
    required this.downloads,
    required this.syncService,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final recentFiles = settings.recentLocalFiles;
    final downloaded = downloads.list();
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
                onPressed: onRetry,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: ElevatedButton.icon(
            onPressed: () => _openLocalFile(context),
            icon: const Icon(Icons.folder_open),
            label: const Text('Open local CBZ file'),
          ),
        ),
        Expanded(
          child: ListView(
            children: [
              if (downloaded.isNotEmpty) ...[
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 0, 16, 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Downloaded', style: TextStyle(color: Colors.white60)),
                  ),
                ),
                ...downloaded.map((d) {
                  final dirty = syncService.store
                      .dirtyItems()
                      .any((p) => p.issueId == d.issueId);
                  return ListTile(
                    leading: const Icon(Icons.check_circle, color: Colors.greenAccent, size: 20),
                    title: Text(
                      d.number != null ? '${d.series} #${d.number}' : d.series,
                      style: const TextStyle(fontSize: 14),
                    ),
                    subtitle: Text(
                      dirty
                          ? 'Downloaded ${_formatAgo(d.downloadedAt)} · Not synced'
                          : 'Downloaded ${_formatAgo(d.downloadedAt)}',
                      style: TextStyle(
                        fontSize: 11,
                        color: dirty ? Colors.amber : Colors.white38,
                      ),
                    ),
                    onTap: () => Navigator.of(context).pushNamed(
                      '/reader/local',
                      arguments: LocalReaderArgs(d.localFilePath, issueId: d.issueId),
                    ),
                  );
                }),
              ],
              if (recentFiles.isNotEmpty) ...[
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 8, 16, 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Recent files', style: TextStyle(color: Colors.white60)),
                  ),
                ),
                ...recentFiles.map((path) => ListTile(
                      leading: const Icon(Icons.book),
                      title: Text(localCbz.titleFromPath(path), style: const TextStyle(fontSize: 14)),
                      subtitle: Text(path, style: const TextStyle(fontSize: 11, color: Colors.white38)),
                      onTap: () => Navigator.of(context).pushNamed(
                        '/reader/local',
                        arguments: LocalReaderArgs(path),
                      ),
                    )),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _openLocalFile(BuildContext context) async {
    final path = await localCbz.pickFile();
    if (path == null || !context.mounted) return;
    settings.addRecentLocalFile(path);
    Navigator.of(context).pushNamed('/reader/local', arguments: LocalReaderArgs(path));
  }

  String _formatAgo(DateTime when) {
    final diff = DateTime.now().toUtc().difference(when);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
