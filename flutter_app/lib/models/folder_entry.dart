// A subfolder shown at one level of Folder View (CUSTOM_TABS_SPEC.md §9) —
// distinct from Issue, which is what a folder's direct file children are.
class FolderEntry {
  final String name;
  final int issueCount;
  final String? coverPath;
  final int? yearMin;
  final int? yearMax;

  const FolderEntry({
    required this.name,
    required this.issueCount,
    this.coverPath,
    this.yearMin,
    this.yearMax,
  });

  factory FolderEntry.fromJson(Map<String, dynamic> json) {
    return FolderEntry(
      name: json['name'] as String,
      issueCount: json['issue_count'] as int? ?? 0,
      coverPath: json['cover_path'] as String?,
      yearMin: json['year_min'] as int?,
      yearMax: json['year_max'] as int?,
    );
  }

  String? get yearLabel {
    if (yearMin == null) return null;
    if (yearMin == yearMax) return '$yearMin';
    return '$yearMin–$yearMax';
  }
}
