class Series {
  final int seriesAnchorId;
  final String name;
  final String? publisher;
  final int? year;
  final List<String> genres;
  final int issueCount;
  final int unreadCount;
  final int readCount;
  final int readingCount;
  final bool favorites;
  final int? personalRating;
  final String coverPath; // e.g. "/api/cover/42"
  final String formatGroup; // "Series" or "Singles"
  final String? summary;
  final int? pageCount; // singles only
  final List<String> writers;

  const Series({
    required this.seriesAnchorId,
    required this.name,
    this.publisher,
    this.year,
    required this.genres,
    required this.issueCount,
    required this.unreadCount,
    required this.readCount,
    required this.readingCount,
    required this.favorites,
    this.personalRating,
    required this.coverPath,
    required this.formatGroup,
    this.summary,
    this.pageCount,
    required this.writers,
  });

  factory Series.fromJson(Map<String, dynamic> json) {
    return Series(
      seriesAnchorId: json['series_anchor_id'] as int,
      name: json['series'] as String,
      publisher: json['publisher'] as String?,
      year: json['year'] as int?,
      genres: List<String>.from(json['genres'] as List? ?? []),
      issueCount: json['issue_count'] as int? ?? 0,
      unreadCount: json['unread_count'] as int? ?? 0,
      readCount: json['read_count'] as int? ?? 0,
      readingCount: json['reading_count'] as int? ?? 0,
      favorites: json['favorites'] as bool? ?? false,
      personalRating: json['personal_rating'] as int?,
      coverPath: json['cover_path'] as String? ?? '',
      formatGroup: json['format_group'] as String? ?? 'Series',
      summary: json['summary'] as String?,
      pageCount: json['page_count'] as int?,
      writers: List<String>.from(json['writers'] as List? ?? []),
    );
  }

  // Mirrors frontend/js/app.js's seriesReadState() so the app and web UI
  // agree on what counts as "unread" / "progress" / "read" for a series.
  String get readState {
    if (issueCount > 0 && readCount == issueCount) return 'read';
    if (readCount > 0 || readingCount > 0) return 'progress';
    return 'unread';
  }

  int get progressPercent =>
      issueCount == 0 ? 0 : ((readCount / issueCount) * 100).round();
}
