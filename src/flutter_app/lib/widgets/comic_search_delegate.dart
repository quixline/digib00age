import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/api_service.dart';

class ComicSearchDelegate extends SearchDelegate<void> {
  final ApiService api;
  ComicSearchDelegate({required this.api});

  @override
  List<Widget> buildActions(BuildContext context) => [
    IconButton(icon: const Icon(Icons.clear), onPressed: () => query = ''),
  ];

  @override
  Widget buildLeading(BuildContext context) =>
      IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => close(context, null));

  @override
  Widget buildResults(BuildContext context) => _buildResultList(context);

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.length < 2) {
      return const Center(child: Text('Type at least 2 characters…', style: TextStyle(color: Colors.white38)));
    }
    return _buildResultList(context);
  }

  Widget _buildResultList(BuildContext context) {
    if (query.length < 2) return const SizedBox.shrink();
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: api.search(query),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text(snap.error.toString(), style: const TextStyle(color: Colors.redAccent)));
        }
        final results = snap.data ?? [];
        if (results.isEmpty) {
          return const Center(child: Text('No results', style: TextStyle(color: Colors.white38)));
        }
        return ListView.builder(
          itemCount: results.length,
          itemBuilder: (context, i) {
            final r = results[i];
            final id = r['id'] as int;
            final series = r['series'] as String;
            final number = r['number'] as String?;
            final coverPath = r['cover_path'] as String? ?? '';
            return ListTile(
              leading: SizedBox(
                width: 32,
                height: 44,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(2),
                  child: CachedNetworkImage(
                    imageUrl: '${api.baseUrl}$coverPath',
                    fit: BoxFit.cover,
                    errorWidget: (_, _, _) => const Icon(Icons.book, size: 20),
                  ),
                ),
              ),
              title: Text(series, style: const TextStyle(fontSize: 14)),
              subtitle: number != null ? Text('#$number') : null,
              onTap: () {
                close(context, null);
                Navigator.of(context, rootNavigator: true).pushNamed('/reader', arguments: id);
              },
            );
          },
        );
      },
    );
  }
}
