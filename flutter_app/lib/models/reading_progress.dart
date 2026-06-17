class ReadingProgress {
  final int issueId;
  final String status; // "unread" | "reading" | "read"
  final int currentPage;
  final DateTime? lastReadAt;

  const ReadingProgress({
    required this.issueId,
    required this.status,
    required this.currentPage,
    this.lastReadAt,
  });

  factory ReadingProgress.fromJson(Map<String, dynamic> json) {
    return ReadingProgress(
      issueId: json['issue_id'] as int,
      status: json['status'] as String? ?? 'unread',
      currentPage: json['current_page'] as int? ?? 0,
      lastReadAt: json['last_read_at'] != null
          ? DateTime.tryParse(json['last_read_at'] as String)
          : null,
    );
  }

  ReadingProgress copyWith({String? status, int? currentPage}) {
    return ReadingProgress(
      issueId: issueId,
      status: status ?? this.status,
      currentPage: currentPage ?? this.currentPage,
      lastReadAt: lastReadAt,
    );
  }
}
