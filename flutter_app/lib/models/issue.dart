class Issue {
  final int id;
  final String series;
  final int? volume;
  final String? number;
  final String? title;
  final int? year;
  final int? month;
  final String? publisher;
  final String? format;
  final String formatGroup;
  final String? summary;
  final String? storyArc;
  final int? storyArcNumber;
  final String? writer;
  final String? penciller;
  final String? inker;
  final String? colorist;
  final String? letterer;
  final String? coverArtist;
  final String? characters;
  final String? teams;
  final String? locations;
  final List<String> genres;
  final String? ageRating;
  final String? language;
  final bool blackAndWhite;
  final String manga; // "No", "Yes", "YesAndRightToLeft"
  final int? pageCount;
  final String coverPath;
  final String readStatus;
  final int currentPage;
  final int? nextIssueId;
  final int? prevIssueId;
  final bool favorites;
  final int? personalRating;

  const Issue({
    required this.id,
    required this.series,
    this.volume,
    this.number,
    this.title,
    this.year,
    this.month,
    this.publisher,
    this.format,
    required this.formatGroup,
    this.summary,
    this.storyArc,
    this.storyArcNumber,
    this.writer,
    this.penciller,
    this.inker,
    this.colorist,
    this.letterer,
    this.coverArtist,
    this.characters,
    this.teams,
    this.locations,
    required this.genres,
    this.ageRating,
    this.language,
    required this.blackAndWhite,
    required this.manga,
    this.pageCount,
    required this.coverPath,
    required this.readStatus,
    required this.currentPage,
    this.nextIssueId,
    this.prevIssueId,
    required this.favorites,
    this.personalRating,
  });

  factory Issue.fromJson(Map<String, dynamic> json) {
    return Issue(
      id: json['id'] as int,
      series: json['series'] as String,
      volume: json['volume'] as int?,
      number: json['number'] as String?,
      title: json['title'] as String?,
      year: json['year'] as int?,
      month: json['month'] as int?,
      publisher: json['publisher'] as String?,
      format: json['format'] as String?,
      formatGroup: json['format_group'] as String? ?? 'Series',
      summary: json['summary'] as String?,
      storyArc: json['story_arc'] as String?,
      storyArcNumber: json['story_arc_number'] as int?,
      writer: json['writer'] as String?,
      penciller: json['penciller'] as String?,
      inker: json['inker'] as String?,
      colorist: json['colorist'] as String?,
      letterer: json['letterer'] as String?,
      coverArtist: json['cover_artist'] as String?,
      characters: json['characters'] as String?,
      teams: json['teams'] as String?,
      locations: json['locations'] as String?,
      genres: List<String>.from(json['genres'] as List? ?? []),
      ageRating: json['age_rating'] as String?,
      language: json['language'] as String?,
      blackAndWhite: json['black_and_white'] as bool? ?? false,
      manga: json['manga'] as String? ?? 'No',
      pageCount: json['page_count'] as int?,
      coverPath: json['cover_path'] as String? ?? '',
      readStatus: json['read_status'] as String? ?? 'unread',
      currentPage: json['current_page'] as int? ?? 0,
      nextIssueId: json['next_issue_id'] as int?,
      prevIssueId: json['prev_issue_id'] as int?,
      favorites: json['favorites'] as bool? ?? false,
      personalRating: json['personal_rating'] as int?,
    );
  }

  bool get isManga => manga == 'YesAndRightToLeft';

  String get displayTitle {
    if (number != null && number!.isNotEmpty) return '#$number';
    return title ?? series;
  }
}

// Lightweight issue summary used in series list and continue-reading strip
class IssueSummary {
  final int id;
  final String series;
  final String? number;
  final String? title;
  final int? year;
  final String? publisher;
  final String? format;
  final String? storyArc;
  final int? storyArcNumber;
  final bool blackAndWhite;
  final bool missing;
  final String coverPath;
  final String readStatus;
  final int currentPage;
  final int? pageCount;

  const IssueSummary({
    required this.id,
    required this.series,
    this.number,
    this.title,
    this.year,
    this.publisher,
    this.format,
    this.storyArc,
    this.storyArcNumber,
    required this.blackAndWhite,
    required this.missing,
    required this.coverPath,
    required this.readStatus,
    required this.currentPage,
    this.pageCount,
  });

  factory IssueSummary.fromJson(Map<String, dynamic> json) {
    return IssueSummary(
      id: json['id'] as int,
      series: json['series'] as String? ?? '',
      number: json['number'] as String?,
      title: json['title'] as String?,
      year: json['year'] as int?,
      publisher: json['publisher'] as String?,
      format: json['format'] as String?,
      storyArc: json['story_arc'] as String?,
      storyArcNumber: json['story_arc_number'] as int?,
      blackAndWhite: json['black_and_white'] as bool? ?? false,
      missing: json['missing'] as bool? ?? false,
      coverPath: json['cover_path'] as String? ?? '',
      readStatus: json['read_status'] as String? ?? 'unread',
      currentPage: json['current_page'] as int? ?? 0,
      pageCount: json['page_count'] as int?,
    );
  }

  String get displayTitle {
    if (number != null && number!.isNotEmpty) return '#$number';
    return title ?? series;
  }
}
