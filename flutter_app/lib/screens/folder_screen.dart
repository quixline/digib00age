// Folder View browse mode (CUSTOM_TABS_SPEC.md §9) for folder-mode custom tabs
// (e.g. "2000 AD"). Mirrors BrowseScreen's grid/card conventions exactly —
// folder tiles and issue-file tiles both render through the shared CoverCard
// widget so they're visually identical to every other library card.
import 'package:flutter/material.dart';
import '../models/folder_entry.dart';
import '../models/issue.dart';
import '../services/api_service.dart';
import '../theme/tokens.dart';
import '../widgets/app_top_bar.dart';
import '../widgets/cover_card.dart';
import '../widgets/page_backdrop.dart';

class FolderFilter {
  final int tabId;
  final String tabName;
  final String path; // "" = root of this tab's folder tree

  const FolderFilter({required this.tabId, required this.tabName, this.path = ''});

  String get currentName => path.isEmpty ? tabName : path.split('/').last;
}

class FolderScreen extends StatefulWidget {
  final ApiService api;
  final FolderFilter filter;
  final VoidCallback onSettingsReturn;

  const FolderScreen({
    super.key,
    required this.api,
    required this.filter,
    required this.onSettingsReturn,
  });

  @override
  State<FolderScreen> createState() => _FolderScreenState();
}

class _FolderScreenState extends State<FolderScreen> {
  List<FolderEntry> _folders = [];
  List<Issue> _files = [];
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
      final contents = await widget.api.getFolderContents(widget.filter.tabId, widget.filter.path);
      if (!mounted) return;
      setState(() { _folders = contents.folders; _files = contents.files; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _openSubfolder(String name) {
    final newPath = widget.filter.path.isEmpty ? name : '${widget.filter.path}/$name';
    Navigator.of(context).pushNamed(
      '/folder',
      arguments: FolderFilter(tabId: widget.filter.tabId, tabName: widget.filter.tabName, path: newPath),
    );
  }

  CoverCardData _folderCard(FolderEntry entry) {
    final meta = [
      if (entry.yearLabel != null) entry.yearLabel!,
      '${entry.issueCount} issue${entry.issueCount == 1 ? '' : 's'}',
    ].join(' · ');
    return CoverCardData(
      title: entry.name,
      meta: meta,
      coverUrl: entry.coverPath == null ? null : '${widget.api.baseUrl}${entry.coverPath}',
      state: 'unread',
      onTap: () => _openSubfolder(entry.name),
    );
  }

  CoverCardData _fileCard(Issue issue) {
    final meta = [
      if (issue.year != null) '${issue.year}',
      if (issue.pageCount != null) '${issue.pageCount} pages',
    ].join(' · ');
    final isProgress = issue.readStatus == 'reading';
    final progressPercent = isProgress && issue.pageCount != null && issue.pageCount! > 0
        ? ((issue.currentPage / issue.pageCount!) * 100).round()
        : 0;
    return CoverCardData(
      title: issue.number != null && issue.number!.isNotEmpty
          ? '${issue.series} #${issue.number}'
          : (issue.title ?? issue.series),
      meta: meta,
      coverUrl: '${widget.api.baseUrl}${issue.coverPath}',
      state: issue.readStatus == 'read' ? 'read' : (isProgress ? 'progress' : 'unread'),
      progressPercent: progressPercent,
      favourite: issue.favorites,
      onTap: () => Navigator.of(context).pushNamed('/issue', arguments: issue.id),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const Positioned.fill(child: PageBackdrop()),
        _buildContent(context),
      ],
    );
  }

  Widget _buildContent(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppTopBar(api: widget.api, onSettingsReturn: widget.onSettingsReturn),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.filter.currentName.toUpperCase(), style: AppText.of(context).eyebrow()),
                    const SizedBox(height: 2),
                    Text(_countLabel(), style: AppText.of(context).countBig()),
                  ],
                ),
              ),
              if (widget.filter.path.isNotEmpty) _BackPill(onTap: () => Navigator.of(context).pop()),
            ],
          ),
        ),
        Expanded(child: _buildBody()),
      ],
    );
  }

  String _countLabel() {
    final n = _folders.length + _files.length;
    return '$n Item${n == 1 ? '' : 's'}';
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
    if (_folders.isEmpty && _files.isEmpty) {
      return const Center(child: Text('No results', style: TextStyle(color: Colors.white38)));
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: GridView.builder(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: AppSpacing.cardMin,
          childAspectRatio: 0.5,
          crossAxisSpacing: AppSpacing.cardGap,
          mainAxisSpacing: AppSpacing.cardGap,
        ),
        itemCount: _folders.length + _files.length,
        itemBuilder: (context, i) {
          if (i < _folders.length) {
            return CoverCard(data: _folderCard(_folders[i]));
          }
          return CoverCard(data: _fileCard(_files[i - _folders.length]));
        },
      ),
    );
  }
}

class _BackPill extends StatelessWidget {
  final VoidCallback onTap;
  const _BackPill({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.of(context).accent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Text('← Back', style: AppText.of(context).label(size: 13, color: Colors.white)),
        ),
      ),
    );
  }
}
