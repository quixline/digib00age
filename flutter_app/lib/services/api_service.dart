import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/series.dart';
import '../models/issue.dart';

class ApiService {
  String baseUrl; // e.g. "http://192.168.1.10:9424"

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

  Future<List<Series>> getLibrary({String? group}) async {
    final uri = Uri.parse('$apiBase/library').replace(
      queryParameters: group != null ? {'group': group} : null,
    );
    final res = await http.get(uri);
    _assertOk(res);
    final list = jsonDecode(res.body) as List;
    return list.map((e) => Series.fromJson(e as Map<String, dynamic>)).toList();
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

  Future<List<Map<String, dynamic>>> get2000adYears() async {
    final res = await http.get(Uri.parse('$apiBase/2000ad/years'));
    _assertOk(res);
    return (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> get2000adYear(int year) async {
    final res = await http.get(Uri.parse('$apiBase/2000ad/year/$year'));
    _assertOk(res);
    return jsonDecode(res.body) as Map<String, dynamic>;
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
