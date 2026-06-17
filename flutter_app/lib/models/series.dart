class Series {
  final int seriesAnchorId;
  final String name;
  final String? publisher;
  final int? year;
  final List<String> genres;
  final int issueCount;
  final int unreadCount;
  final String coverPath; // e.g. "/api/cover/42"
  final String formatGroup; // "Series" or "Singles"

  const Series({
    required this.seriesAnchorId,
    required this.name,
    this.publisher,
    this.year,
    required this.genres,
    required this.issueCount,
    required this.unreadCount,
    required this.coverPath,
    required this.formatGroup,
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
      coverPath: json['cover_path'] as String? ?? '',
      formatGroup: json['format_group'] as String? ?? 'Series',
    );
  }
}
