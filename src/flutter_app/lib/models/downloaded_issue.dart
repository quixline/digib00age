class DownloadedIssue {
  final int issueId;
  final String series;
  final String? number;
  final String? title;
  final String localFilePath;
  final int pageCount;
  final DateTime downloadedAt;

  DownloadedIssue({
    required this.issueId,
    required this.series,
    this.number,
    this.title,
    required this.localFilePath,
    required this.pageCount,
    required this.downloadedAt,
  });

  Map<String, dynamic> toJson() => {
        'issueId': issueId,
        'series': series,
        'number': number,
        'title': title,
        'localFilePath': localFilePath,
        'pageCount': pageCount,
        'downloadedAt': downloadedAt.toIso8601String(),
      };

  factory DownloadedIssue.fromJson(Map<String, dynamic> j) => DownloadedIssue(
        issueId: j['issueId'] as int,
        series: j['series'] as String,
        number: j['number'] as String?,
        title: j['title'] as String?,
        localFilePath: j['localFilePath'] as String,
        pageCount: j['pageCount'] as int,
        downloadedAt: DateTime.parse(j['downloadedAt'] as String),
      );
}
