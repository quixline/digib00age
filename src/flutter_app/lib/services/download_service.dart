import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../models/downloaded_issue.dart';
import 'api_service.dart';
import 'local_cbz_service.dart';
import 'settings_service.dart';

// Manages the set of comics fetched from the server for offline reading —
// the download HTTP call, the local manifest, and deletion. Distinct from
// LocalCbzService, which just reads bytes from whatever archive path it's
// given (arbitrary picked file or a download managed here, it doesn't care).
class DownloadService {
  final ApiService api;
  final SettingsService settings;
  final LocalCbzService localCbz;

  DownloadService(this.api, this.settings, this.localCbz);

  static const _manifestKey = 'downloaded_issues';

  List<DownloadedIssue> list() {
    final raw = settings.prefs.getStringList(_manifestKey) ?? [];
    return raw
        .map((s) => DownloadedIssue.fromJson(jsonDecode(s) as Map<String, dynamic>))
        .toList();
  }

  DownloadedIssue? findByIssueId(int issueId) {
    for (final d in list()) {
      if (d.issueId == issueId) return d;
    }
    return null;
  }

  Future<DownloadedIssue> download(
    int issueId, {
    required String series,
    String? number,
    String? title,
  }) async {
    final (bytes, ext) = await api.downloadIssue(issueId);
    final dir = await getApplicationDocumentsDirectory();
    final path = p.join(dir.path, 'downloads', '$issueId$ext');
    await Directory(p.dirname(path)).create(recursive: true);
    await File(path).writeAsBytes(bytes);

    int pageCount;
    try {
      pageCount = localCbz.listPages(path).length;
    } catch (e) {
      // CBR isn't decodable locally — LocalCbzService only supports
      // ZipDecoder (see its own docstring / SPEC.md's "Flutter local/offline
      // mode is a known, accepted gap"). Don't leave an unreadable file +
      // manifest entry behind; surface a clear reason instead of the raw
      // archive-decode exception.
      try {
        await File(path).delete();
      } catch (_) {}
      if (ext == '.cbr') {
        throw Exception('CBR issues can\'t be read offline yet — only CBZ is supported.');
      }
      rethrow;
    }

    final entry = DownloadedIssue(
      issueId: issueId,
      series: series,
      number: number,
      title: title,
      localFilePath: path,
      pageCount: pageCount,
      downloadedAt: DateTime.now().toUtc(),
    );
    _save(entry);
    return entry;
  }

  void _save(DownloadedIssue entry) {
    final all = list().where((d) => d.issueId != entry.issueId).toList()..add(entry);
    settings.prefs.setStringList(
      _manifestKey,
      all.map((d) => jsonEncode(d.toJson())).toList(),
    );
  }

  Future<void> delete(int issueId) async {
    final entry = findByIssueId(issueId);
    if (entry == null) return;
    try {
      await File(entry.localFilePath).delete();
    } catch (_) {
      // File already gone / inaccessible — manifest cleanup still proceeds.
    }
    final remaining = list().where((d) => d.issueId != issueId).toList();
    settings.prefs.setStringList(
      _manifestKey,
      remaining.map((d) => jsonEncode(d.toJson())).toList(),
    );
  }
}
