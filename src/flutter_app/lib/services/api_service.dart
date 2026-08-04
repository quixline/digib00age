import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/series.dart';
import '../models/issue.dart';
import '../models/custom_tab.dart';
import '../models/folder_entry.dart';

class ApiService {
  String baseUrl; // e.g. "http://192.168.1.10:9800"

  ApiService(this.baseUrl);

  String get apiBase => '$baseUrl/api';

  String coverUrl(int issueId) => '$apiBase/cover/$issueId';
  String pageUrl(int issueId, int pageNumber) => '$apiBase/page/$issueId/$pageNumber';

  // Returns true if the server responds within 3 seconds.
  // Uses /api/ping rather than an /api/admin/* route — the admin routes sit
  // behind require_admin_auth, which rejects any non-local request outright
  // when Remote Administration is off (the default), so a LAN client like the
  // Flutter app would always read as "offline" even with a healthy server (BUG-019).
  Future<bool> checkConnection() async {
    try {
      final res = await http
          .get(Uri.parse('$apiBase/ping'))
          .timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<List<Series>> getLibrary({
    String? group,
    int? tabId,
    String? field,
    String? value,
    String? q,
  }) async {
    final params = <String, String>{
      'group': ?group,
      'tab_id': ?tabId?.toString(),
      'field': ?field,
      'value': ?value,
      'q': ?q,
    };
    final uri = Uri.parse('$apiBase/library')
        .replace(queryParameters: params.isEmpty ? null : params);
    final res = await http.get(uri);
    _assertOk(res);
    final list = jsonDecode(res.body) as List;
    return list.map((e) => Series.fromJson(e as Map<String, dynamic>)).toList();
  }

  // Visible custom tabs (CUSTOM_TABS_SPEC.md) for the nav rail's Libraries
  // section, in creation order.
  Future<List<CustomTabInfo>> getNavConfig() async {
    final res = await http.get(Uri.parse('$apiBase/nav/config'));
    _assertOk(res);
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['custom_tabs'] as List)
        .map((e) => CustomTabInfo.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // Folder View browse mode (CUSTOM_TABS_SPEC.md §9) — one directory level
  // under a folder-mode custom tab's root. `files` reuses the same shape
  // /api/issue/{id} returns, so Issue.fromJson parses it directly.
  Future<({List<FolderEntry> folders, List<Issue> files})> getFolderContents(
    int tabId,
    String path,
  ) async {
    final uri = Uri.parse('$apiBase/library/tab/$tabId/folder')
        .replace(queryParameters: {'path': path});
    final res = await http.get(uri);
    _assertOk(res);
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    final folders = (body['folders'] as List)
        .map((e) => FolderEntry.fromJson(e as Map<String, dynamic>))
        .toList();
    final files = (body['files'] as List)
        .map((e) => Issue.fromJson(e as Map<String, dynamic>))
        .toList();
    return (folders: folders, files: files);
  }

  // Home page strips (HOME_STRIPS_SPEC.md) — defaults + admin-added.
  Future<List<Map<String, dynamic>>> getHomeStrips() async {
    final res = await http.get(Uri.parse('$apiBase/home/strips'));
    _assertOk(res);
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['strips'] as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getSeriesDetail(int anchorId) async {
    final res = await http.get(Uri.parse('$apiBase/series/$anchorId'));
    _assertOk(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Issue> getIssue(int id) async {
    final res = await http.get(Uri.parse('$apiBase/issue/$id'));
    _assertOk(res);
    return Issue.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> getPages(int issueId) async {
    final res = await http.get(Uri.parse('$apiBase/issue/$issueId/pages'));
    _assertOk(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getContinueReading() async {
    final res = await http.get(Uri.parse('$apiBase/reading/continue'));
    _assertOk(res);
    return (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> search(String query) async {
    final uri = Uri.parse('$apiBase/search').replace(
      queryParameters: {'q': query},
    );
    final res = await http.get(uri);
    _assertOk(res);
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['results'] as List).cast<Map<String, dynamic>>();
  }

  Future<void> updateProgress(int issueId, {String? status, int? currentPage}) async {
    final body = <String, dynamic>{};
    if (status != null) body['status'] = status;
    if (currentPage != null) body['current_page'] = currentPage;
    await http.post(
      Uri.parse('$apiBase/progress/$issueId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    // Intentionally swallow errors — progress is best-effort
  }

  Future<void> markRead(int issueId) async {
    await http.post(Uri.parse('$apiBase/progress/$issueId/mark-read'));
  }

  Future<void> markUnread(int issueId) async {
    await http.post(Uri.parse('$apiBase/progress/$issueId/mark-unread'));
  }

  // No single-issue favourite/rating endpoint exists — reuse the bulk
  // endpoints with a one-element id list.
  Future<void> toggleFavorite(int issueId, bool favorite) async {
    final path = favorite ? 'favorite' : 'unfavorite';
    await http.post(
      Uri.parse('$apiBase/progress/bulk/$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'issue_ids': [issueId]}),
    );
  }

  Future<void> setRating(int issueId, int rating) async {
    await http.post(
      Uri.parse('$apiBase/progress/bulk/rate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'issue_ids': [issueId], 'rating': rating}),
    );
  }

  // Fetches the whole CBZ/CBR file for offline download (v2.5 Item 3).
  // Returns the raw bytes plus the real extension (from Content-Type, which
  // backend/routers/reader.py's download_issue() sets per the actual file —
  // ".cbz" or ".cbr") so the caller never mislabels a CBR download as a CBZ.
  Future<(List<int> bytes, String extension)> downloadIssue(int issueId) async {
    final res = await http.get(Uri.parse('$apiBase/issue/$issueId/download'));
    _assertOk(res);
    final contentType = res.headers['content-type'] ?? '';
    final ext = contentType.contains('cbr') ? '.cbr' : '.cbz';
    return (res.bodyBytes, ext);
  }

  // Batch-reconciles offline-captured progress against the server
  // (v2.5 Item 3) — see backend/routers/sync.py for the conflict rule.
  Future<Map<String, dynamic>> syncProgress(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$apiBase/sync/progress'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    _assertOk(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getPublishers() async {
    final res = await http.get(Uri.parse('$apiBase/browse/publishers'));
    _assertOk(res);
    return (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> getGenres() async {
    final res = await http.get(Uri.parse('$apiBase/browse/genres'));
    _assertOk(res);
    return (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getAdminStats() async {
    final res = await http.get(Uri.parse('$apiBase/admin/stats'));
    _assertOk(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  void _assertOk(http.Response res) {
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw ApiException(res.statusCode, res.body);
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String body;
  ApiException(this.statusCode, this.body);

  @override
  String toString() => 'ApiException($statusCode): $body';
}
