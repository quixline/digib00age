import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/tokens.dart';
import '../widgets/cover_card.dart';
import '../widgets/app_top_bar.dart';
import '../widgets/page_backdrop.dart';

class HomeScreen extends StatefulWidget {
  final ApiService api;
  final VoidCallback onSettingsReturn;
  const HomeScreen({super.key, required this.api, required this.onSettingsReturn});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _strips = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final strips = await widget.api.getHomeStrips();
      if (!mounted) return;
      setState(() { _strips = strips; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const Positioned.fill(child: PageBackdrop()),
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppTopBar(api: widget.api, onSettingsReturn: widget.onSettingsReturn),
            Expanded(child: _buildBody()),
          ],
        ),
      ],
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.only(top: 8, bottom: 40),
        itemCount: _strips.length,
        itemBuilder: (context, i) => _StripRow(strip: _strips[i], api: widget.api),
      ),
    );
  }
}

class _StripRow extends StatelessWidget {
  final Map<String, dynamic> strip;
  final ApiService api;

  const _StripRow({required this.strip, required this.api});

  @override
  Widget build(BuildContext context) {
    final title = strip['title'] as String? ?? '';
    final items = (strip['items'] as List? ?? []).cast<Map<String, dynamic>>();
    if (items.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 14, 20, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: AppText.of(context).eyebrow()),
          const SizedBox(height: 14),
          SizedBox(
            height: 300,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(width: 14),
              itemBuilder: (context, i) => SizedBox(
                width: 150,
                child: CoverCard(data: _cardFor(context, items[i])),
              ),
            ),
          ),
        ],
      ),
    );
  }

  CoverCardData _cardFor(BuildContext context, Map<String, dynamic> card) {
    final id = card['id'] as int;
    final series = card['series'] as String? ?? '';
    final number = card['number'] as String?;
    final year = card['year'] as int?;
    final formatGroup = card['format_group'] as String? ?? 'Series';
    final coverPath = card['cover_path'] as String? ?? '';
    final readStatus = card['read_status'] as String? ?? 'unread';
    final currentPage = card['current_page'] as int? ?? 0;
    final pageCount = card['page_count'] as int?;

    final title = number != null && number.isNotEmpty ? '$series #$number' : series;
    final meta = formatGroup == 'Singles' && pageCount != null
        ? [if (year != null) '$year', '$pageCount pages'].join(' · ')
        : (year != null ? '$year' : '');

    final state = readStatus == 'read' ? 'read' : (readStatus == 'reading' ? 'progress' : 'unread');
    final progressPercent = (pageCount != null && pageCount > 0)
        ? ((currentPage / pageCount) * 100).round()
        : 0;

    return CoverCardData(
      title: title,
      meta: meta,
      coverUrl: '${api.baseUrl}$coverPath',
      state: state,
      progressPercent: progressPercent,
      onTap: () {
        if (formatGroup == 'Singles') {
          Navigator.of(context).pushNamed('/issue', arguments: id);
        } else {
          Navigator.of(context).pushNamed('/series', arguments: id);
        }
      },
    );
  }
}
