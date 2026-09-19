import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/issue.dart';
import '../services/api_service.dart';
import '../services/settings_service.dart';
import '../services/local_cbz_service.dart';
import '../services/sync_store.dart';
import '../services/download_service.dart';
import '../services/sync_service.dart';
import '../models/downloaded_issue.dart';
import '../widgets/comic_page_view.dart';
import '../widgets/toolbar_overlay.dart';
import '../theme/tokens.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Server-mode reader
// ─────────────────────────────────────────────────────────────────────────────

class ReaderScreen extends StatefulWidget {
  final int issueId;
  final ApiService api;
  final SettingsService settings;

  const ReaderScreen({
    super.key,
    required this.issueId,
    required this.api,
    required this.settings,
  });

  @override
  State<ReaderScreen> createState() => _ReaderScreenState();
}

class _ReaderScreenState extends State<ReaderScreen> {
  final _pageViewKey = GlobalKey<ComicPageViewState>();

  Issue? _issue;
  List<String> _pageUrls = [];
  bool _loading = true;
  String? _error;
  int _currentPage = 0;
  late ReadingMode _mode;

  @override
  void initState() {
    super.initState();
    _mode = widget.settings.readingMode == 'page' ? ReadingMode.page : ReadingMode.scroll;
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    _load();
  }

  // Deliberately doesn't restore edgeToEdge here — see build()'s PopScope
  // instead. pushReplacementNamed (advancing to the next issue) disposes
  // this screen too, but its MaterialPageRoute transition means dispose()
  // here can run AFTER the new ReaderScreen's initState() has already
  // re-asserted immersiveSticky, silently undoing it and leaving system UI
  // (status bar +, on some devices, a persistent nav dock) visible for the
  // rest of the reading session. Restoring only on an actual pop (via
  // PopScope, which fires deterministically before disposal) means a
  // same-series issue-to-issue advance never toggles system UI at all.
  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        widget.api.getIssue(widget.issueId),
        widget.api.getPages(widget.issueId),
      ]);
      final issue = results[0] as Issue;
      final pagesData = results[1] as Map<String, dynamic>;
      final pageCount = pagesData['page_count'] as int;
      final urls = List.generate(pageCount, (i) => widget.api.pageUrl(widget.issueId, i));
      if (!mounted) return;
      setState(() {
        _issue = issue;
        _pageUrls = urls;
        _currentPage = issue.currentPage.clamp(0, (pageCount - 1).clamp(0, 999999));
        _loading = false;
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _onPageChanged(int page) {
    setState(() => _currentPage = page);
    widget.api.updateProgress(
      widget.issueId,
      currentPage: page,
      status: page == _pageUrls.length - 1 ? 'read' : null,
    );
  }

  void _onModeChanged(ReadingMode m) {
    setState(() => _mode = m);
    _pageViewKey.currentState?.resetZoom();
  }

  void _onPrevPage() => _pageViewKey.currentState?.prevPage();

  // Reaching the last page no longer auto-pops the next-issue sheet (it used
  // to fire the instant _onPageChanged saw the last index, however the user
  // got there — swipe, scroll estimate, or slider drag — which interrupted
  // reading that page's own content). It now only shows when the reader
  // deliberately tries to advance past the last page: tapping this button,
  // or an overscroll attempt (see onOverscrollNext below). Mirrors the web
  // reader's goNext() fix (commit d5bf08d).
  void _onNextPage() {
    if (_currentPage == _pageUrls.length - 1) {
      _showNextIssuePrompt();
      return;
    }
    _pageViewKey.currentState?.nextPage();
  }

  void _onDoubleTapMiddle() => _pageViewKey.currentState?.toggleZoom();

  void _handleOverscrollNext() {
    if (_currentPage == _pageUrls.length - 1) _showNextIssuePrompt();
  }

  bool _nextPromptOpen = false;

  void _showNextIssuePrompt() {
    if (_nextPromptOpen || _issue?.nextIssueId == null) return;
    final nextId = _issue!.nextIssueId!;
    _nextPromptOpen = true;
    showDialog<void>(
      context: context,
      builder: (_) => _NextIssueDialog(
        nextIssueId: nextId,
        api: widget.api,
        onOpen: () {
          Navigator.of(context).pop();
          Navigator.of(context).pushReplacementNamed('/reader', arguments: nextId);
        },
      ),
    ).whenComplete(() => _nextPromptOpen = false);
  }

  @override
  Widget build(BuildContext context) {
    final Widget body;
    if (_loading) {
      body = const Scaffold(body: Center(child: CircularProgressIndicator()));
    } else if (_error != null) {
      body = Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, style: const TextStyle(color: Colors.redAccent)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _load, child: const Text('Retry')),
            ],
          ),
        ),
      );
    } else {
      final issue = _issue!;
      final pageCount = _pageUrls.length;
      final label = issue.number != null ? '${issue.series} #${issue.number}' : issue.series;

      body = Scaffold(
        backgroundColor: Colors.black,
        body: ToolbarOverlay(
          mode: _mode,
          onPrevPage: _onPrevPage,
          onNextPage: _onNextPage,
          onDoubleTapMiddle: _onDoubleTapMiddle,
          onBack: () => Navigator.of(context).pop(),
          topBar: _TopBar(
            title: label,
            currentPage: _currentPage,
            pageCount: pageCount,
            onBack: () => Navigator.of(context).pop(),
          ),
          bottomBar: _BottomBar(
            currentPage: _currentPage,
            pageCount: pageCount,
            mode: _mode,
            onModeChanged: _onModeChanged,
            onSliderChanged: (v) {
              setState(() => _currentPage = v);
              _pageViewKey.currentState?.jumpToPage(v);
            },
          ),
          child: ComicPageView(
            key: _pageViewKey,
            pageUrls: _pageUrls,
            mode: _mode,
            reversePages: issue.isManga,
            initialPage: _currentPage,
            onPageChanged: _onPageChanged,
            onOverscrollNext: _handleOverscrollNext,
          ),
        ),
      );
    }
    // Only restore system UI on an actual pop — see the note on dispose()
    // above for why that (not dispose) is the reliable place to do it.
    return PopScope(
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
      },
      child: body,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Local file reader
// ─────────────────────────────────────────────────────────────────────────────

// Route arguments for '/reader/local'. issueId is only set when opening a
// DownloadedIssue (v2.5 Item 3) — arbitrary files picked via the file picker
// or "Open With" pass issueId: null and behave exactly as before this item.
class LocalReaderArgs {
  final String filePath;
  final int? issueId;
  const LocalReaderArgs(this.filePath, {this.issueId});
}

// Adjacency order for downloaded issues of one series — the offline
// equivalent of the backend's _find_adjacent_issue sort_key
// (src/backend/routers/library.py), since there's no server to ask offline.
// Numeric-parseable numbers sort first by value; anything else falls back to
// issueId so the order is at least stable.
int _compareDownloaded(DownloadedIssue a, DownloadedIssue b) {
  int rank(DownloadedIssue d) => double.tryParse(d.number ?? '') != null ? 0 : 1;
  final ra = rank(a), rb = rank(b);
  if (ra != rb) return ra.compareTo(rb);
  if (ra == 0) {
    final cmp = double.parse(a.number!).compareTo(double.parse(b.number!));
    if (cmp != 0) return cmp;
  }
  return a.issueId.compareTo(b.issueId);
}

class LocalReaderScreen extends StatefulWidget {
  final String filePath;
  final SettingsService settings;
  final LocalCbzService localCbz;
  final int? issueId;
  final SyncStore? syncStore; // required iff issueId != null
  final DownloadService? downloads; // required iff issueId != null
  final SyncService? syncService; // required iff issueId != null

  const LocalReaderScreen({
    super.key,
    required this.filePath,
    required this.settings,
    required this.localCbz,
    this.issueId,
    this.syncStore,
    this.downloads,
    this.syncService,
  });

  @override
  State<LocalReaderScreen> createState() => _LocalReaderScreenState();
}

class _LocalReaderScreenState extends State<LocalReaderScreen> {
  final _pageViewKey = GlobalKey<LocalComicPageViewState>();

  int _pageCount = 0;
  bool _loading = true;
  String? _error;
  int _currentPage = 0;
  late ReadingMode _mode;
  DownloadedIssue? _nextDownloaded;

  @override
  void initState() {
    super.initState();
    _mode = widget.settings.readingMode == 'page' ? ReadingMode.page : ReadingMode.scroll;
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    _load();
  }

  // See ReaderScreen.dispose() — same reasoning, same fix: restore system UI
  // only on an actual pop (PopScope, in build()), never here.
  @override
  void dispose() {
    widget.localCbz.clear();
    super.dispose();
  }

  // Only counts pages up front — LocalComicPageView reads each page's bytes
  // on demand as it's built. Eagerly decoding every page here (as this used
  // to) held the whole issue's worth of image bytes in memory at once; for a
  // large CBZ that was enough sustained memory pressure to get the app killed
  // by Android's low-memory killer shortly after opening, even once BUG-020's
  // pick-time OOM crash was fixed (docs/archive/bugs-fixed-archive.md).
  Future<void> _load() async {
    try {
      final pageCount = widget.localCbz.listPages(widget.filePath).length;
      final saved = widget.settings.getLocalProgress(widget.filePath);
      if (!mounted) return;
      setState(() {
        _pageCount = pageCount;
        _currentPage = saved?.currentPage ?? 0;
        _loading = false;
        _nextDownloaded = _findNextDownloaded();
      });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  // Offline counterpart of the server's next_issue_id: since there's no
  // network to ask "what's next in this series", the only issues it can ever
  // offer are ones already downloaded to this device — never issues that
  // exist in the library but haven't been downloaded yet.
  DownloadedIssue? _findNextDownloaded() {
    if (widget.issueId == null || widget.downloads == null) return null;
    final current = widget.downloads!.findByIssueId(widget.issueId!);
    if (current == null) return null;
    final siblings = widget.downloads!.list()
        .where((d) => d.series == current.series)
        .toList()
      ..sort(_compareDownloaded);
    final idx = siblings.indexWhere((d) => d.issueId == current.issueId);
    if (idx == -1 || idx + 1 >= siblings.length) return null;
    return siblings[idx + 1];
  }

  void _onPageChanged(int page) {
    setState(() => _currentPage = page);
    widget.settings.saveLocalProgress(widget.filePath, page, _pageCount);
    if (widget.issueId != null) {
      widget.syncStore!.recordProgress(
        widget.issueId!,
        currentPage: page,
        status: page == _pageCount - 1 ? 'read' : 'reading',
      );
    }
  }

  void _onModeChanged(ReadingMode m) {
    setState(() => _mode = m);
    _pageViewKey.currentState?.resetZoom();
  }

  void _onPrevPage() => _pageViewKey.currentState?.prevPage();

  // See ReaderScreen._onNextPage — same fix, same reasoning: only offer the
  // next issue on a deliberate advance attempt, never automatically on
  // arrival at the last page.
  void _onNextPage() {
    if (_currentPage == _pageCount - 1 && _nextDownloaded != null) {
      _showNextIssuePrompt();
      return;
    }
    _pageViewKey.currentState?.nextPage();
  }

  void _onDoubleTapMiddle() => _pageViewKey.currentState?.toggleZoom();

  void _handleOverscrollNext() {
    if (_currentPage == _pageCount - 1) _showNextIssuePrompt();
  }

  bool _nextPromptOpen = false;

  void _showNextIssuePrompt() {
    final next = _nextDownloaded;
    if (_nextPromptOpen || next == null) return;
    _nextPromptOpen = true;
    showDialog<void>(
      context: context,
      builder: (_) => _NextIssueDialog(
        series: next.series,
        number: next.number,
        onOpen: () {
          Navigator.of(context).pop();
          // Best-effort: flush any queued offline progress the moment we
          // have a chance, without waiting for the user to back out to the
          // shell (the only other place a sync is currently triggered).
          // Safe to fire-and-forget — syncNow() already degrades gracefully
          // when there's no connection.
          widget.syncService?.syncNow();
          Navigator.of(context).pushReplacementNamed(
            '/reader/local',
            arguments: LocalReaderArgs(next.localFilePath, issueId: next.issueId),
          );
        },
      ),
    ).whenComplete(() => _nextPromptOpen = false);
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.localCbz.titleFromPath(widget.filePath);
    final Widget body;

    if (_loading) {
      body = Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 12),
              Text(title, style: const TextStyle(color: Colors.white54)),
            ],
          ),
        ),
      );
    } else if (_error != null) {
      body = Scaffold(
        body: Center(child: Text(_error!, style: const TextStyle(color: Colors.redAccent))),
      );
    } else {
      final pageCount = _pageCount;

      body = Scaffold(
        backgroundColor: Colors.black,
        body: ToolbarOverlay(
          mode: _mode,
          onPrevPage: _onPrevPage,
          onNextPage: _onNextPage,
          onDoubleTapMiddle: _onDoubleTapMiddle,
          onBack: () => Navigator.of(context).pop(),
          topBar: _TopBar(
            title: title,
            currentPage: _currentPage,
            pageCount: pageCount,
            onBack: () => Navigator.of(context).pop(),
          ),
          bottomBar: _BottomBar(
            currentPage: _currentPage,
            pageCount: pageCount,
            mode: _mode,
            onModeChanged: _onModeChanged,
            onSliderChanged: (v) {
              setState(() => _currentPage = v);
              _pageViewKey.currentState?.jumpToPage(v);
            },
          ),
          child: LocalComicPageView(
            key: _pageViewKey,
            filePath: widget.filePath,
            localCbz: widget.localCbz,
            pageCount: pageCount,
            mode: _mode,
            reversePages: false,
            initialPage: _currentPage,
            onPageChanged: _onPageChanged,
            onOverscrollNext: _handleOverscrollNext,
          ),
        ),
      );
    }
    return PopScope(
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
      },
      child: body,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared toolbar widgets
// ─────────────────────────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  final String title;
  final int currentPage;
  final int pageCount;
  final VoidCallback onBack;

  const _TopBar({
    required this.title,
    required this.currentPage,
    required this.pageCount,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.black87, Colors.transparent],
        ),
      ),
      padding: EdgeInsets.fromLTRB(
        8,
        MediaQuery.of(context).padding.top + 4,
        16,
        16,
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: onBack,
          ),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Text(
            '${currentPage + 1} / $pageCount',
            style: const TextStyle(color: Colors.white60, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  final int currentPage;
  final int pageCount;
  final ReadingMode mode;
  final ValueChanged<ReadingMode> onModeChanged;
  final ValueChanged<int> onSliderChanged;

  const _BottomBar({
    required this.currentPage,
    required this.pageCount,
    required this.mode,
    required this.onModeChanged,
    required this.onSliderChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Colors.black87, Colors.transparent],
        ),
      ),
      padding: EdgeInsets.fromLTRB(
        16,
        16,
        16,
        MediaQuery.of(context).padding.bottom + 12,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (pageCount > 1)
            Slider(
              value: currentPage.toDouble(),
              min: 0,
              max: (pageCount - 1).toDouble(),
              divisions: pageCount > 1 ? pageCount - 1 : null,
              onChanged: (v) => onSliderChanged(v.round()),
            ),
          const SizedBox(height: 4),
          // Mode toggle — segmented pill control
          Container(
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(28),
              border: Border.all(color: Colors.white24),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _ModeButton(
                  icon: Icons.swap_vert,
                  label: 'Scroll',
                  selected: mode == ReadingMode.scroll,
                  onTap: () => onModeChanged(ReadingMode.scroll),
                ),
                _ModeButton(
                  icon: Icons.chrome_reader_mode,
                  label: 'Page',
                  selected: mode == ReadingMode.page,
                  onTap: () => onModeChanged(ReadingMode.page),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ModeButton({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 11),
        decoration: BoxDecoration(
          color: selected ? Colors.white.withValues(alpha: 0.22) : Colors.transparent,
          borderRadius: BorderRadius.circular(26),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 22,
              color: selected ? Colors.white : Colors.white38,
            ),
            const SizedBox(width: 7),
            Text(
              label,
              style: TextStyle(
                fontSize: 15,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                color: selected ? Colors.white : Colors.white38,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Next issue prompt
// ─────────────────────────────────────────────────────────────────────────────

class _NextIssueDialog extends StatefulWidget {
  // Online (ReaderScreen) passes nextIssueId + api and lets this widget fetch
  // the next issue's series/number itself. Offline (LocalReaderScreen)
  // already has that data locally (no network available to fetch with), so
  // it passes series/number directly and skips the fetch entirely.
  final int? nextIssueId;
  final ApiService? api;
  final String? series;
  final String? number;
  final VoidCallback onOpen;

  const _NextIssueDialog({
    this.nextIssueId,
    this.api,
    this.series,
    this.number,
    required this.onOpen,
  }) : assert(series != null || (nextIssueId != null && api != null));

  @override
  State<_NextIssueDialog> createState() => _NextIssueDialogState();
}

class _NextIssueDialogState extends State<_NextIssueDialog> {
  Map<String, dynamic>? _issueData;

  @override
  void initState() {
    super.initState();
    if (widget.series != null) {
      _issueData = {'series': widget.series, 'number': widget.number};
    } else {
      _loadNext();
    }
  }

  Future<void> _loadNext() async {
    try {
      final issue = await widget.api!.getIssue(widget.nextIssueId!);
      if (mounted) {
        setState(() => _issueData = {
          'series': issue.series,
          'number': issue.number,
        });
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final series = _issueData?['series'] as String? ?? '…';
    final number = _issueData?['number'] as String?;
    final colors = AppColors.of(context);
    // Centered rather than pinned to the bottom: a bottom sheet's buttons can
    // end up underneath a device's own system UI (status bar, or on some OEM
    // tablets a persistent nav dock) if that reclaims screen space after a
    // route transition. A centered dialog isn't anchored to either screen
    // edge, so it's never exposed to that class of problem regardless of
    // platform/device — the real fix for that is ReaderScreen/
    // LocalReaderScreen's PopScope-based system-UI handling; this is the
    // second, independent layer that makes the prompt itself robust too.
    return Dialog(
      backgroundColor: colors.surfaceRaised,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle, color: Colors.greenAccent, size: 40),
            const SizedBox(height: 12),
            Text(
              'Issue complete',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: colors.textPrimary),
            ),
            const SizedBox(height: 8),
            Text(
              number != null ? 'Up next: $series #$number' : 'Up next: $series',
              style: TextStyle(color: colors.textSecondary),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Stay here'),
                ),
                FilledButton.icon(
                  onPressed: widget.onOpen,
                  icon: const Icon(Icons.arrow_forward),
                  label: const Text('Next issue'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
