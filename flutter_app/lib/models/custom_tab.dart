class CustomTabInfo {
  final int id;
  final String name;
  final String viewMode; // "flat" | "folder"
  final String basisType; // "folder" | "favorites"

  const CustomTabInfo({
    required this.id,
    required this.name,
    required this.viewMode,
    required this.basisType,
  });

  factory CustomTabInfo.fromJson(Map<String, dynamic> json) {
    return CustomTabInfo(
      id: json['id'] as int,
      name: json['name'] as String,
      viewMode: json['view_mode'] as String? ?? 'flat',
      basisType: json['basis_type'] as String? ?? 'folder',
    );
  }

  // Collapsed-rail circle glyph: '#' for names starting with a digit
  // (e.g. "2000 AD"), else the uppercased first letter.
  String get firstLetterGlyph {
    if (name.isEmpty) return '#';
    final first = name[0];
    return RegExp(r'[0-9]').hasMatch(first) ? '#' : first.toUpperCase();
  }
}
