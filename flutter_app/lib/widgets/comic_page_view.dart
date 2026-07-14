import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../services/local_cbz_service.dart';

enum ReadingMode { scroll, page }

// ─────────────────────────────────────────────────────────────────────────────
// Server-mode reader (URL-based pages)
// ─────────────────────────────────────────────────────────────────────────────

class ComicPageView extends StatefulWidget {
  final List<String> pageUrls;
  final ReadingMode mode;
  final bool reversePages;
  final int initialPage;
  final ValueChanged<int> onPageChanged;

  const ComicPageView({
    super.key,
    required this.pageUrls,
    required this.mode,
    required this.reversePages,
    required this.initialPage,
    required this.onPageChanged,
  });

  @override
  State<ComicPageView> createState() => ComicPageViewState();
}

class ComicPageViewState extends State<ComicPageView> {
  late PageController _pageController;
  late ScrollController _scrollController;
  late TransformationController _transformController;

  bool _zoomedToWidth = false;
  BoxConstraints? _pageConstraints;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: widget.initialPage);
    _scrollController = ScrollController();
    _transformController = TransformationController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _scrollController.dispose();
    _transformController.dispose();
    super.dispose();
  }

  // ── Public API (called via GlobalKey from ReaderScreen) ───────────────────

  // In scroll mode _pageController isn't attached to anything (the ListView
  // uses _scrollController instead) — these double as the keyboard/desktop
  // "page" gesture for continuous-scroll mode, animating by one viewport.
  void nextPage() {
    if (widget.mode == ReadingMode.scroll) {
      _scrollByViewport(1);
      return;
    }
    _pageController.nextPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void prevPage() {
    if (widget.mode == ReadingMode.scroll) {
      _scrollByViewport(-1);
      return;
    }
    _pageController.previousPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void _scrollByViewport(int direction) {
    if (!_scrollController.hasClients) return;
    final position = _scrollController.position;
    final target = (position.pixels + direction * position.viewportDimension * 0.9)
        .clamp(position.minScrollExtent, position.maxScrollExtent);
    _scrollController.animateTo(
      target,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void jumpToPage(int page) {
    resetZoom();
    if (widget.mode == ReadingMode.page) {
      _pageController.jumpToPage(page);
    }
  }

  void resetZoom() {
    _transformController.value = Matrix4.identity();
    _zoomedToWidth = false;
  }

  // Double-tap: toggle between fit-whole-page (identity) and fit-to-width.
  // Scale is calculated from the current LayoutBuilder constraints assuming a
  // portrait comic page — works best in landscape orientation.
  void toggleZoom() {
    final c = _pageConstraints;
    if (c == null) return;

    if (_zoomedToWidth) {
      _transformController.value = Matrix4.identity();
      _zoomedToWidth = false;
    } else {
      // Portrait comic ≈ 2:3. When height-constrained (landscape), the displayed
      // width = containerHeight * (2/3). Scale to fill containerWidth.
      final scale = (3 * c.maxWidth / (2 * c.maxHeight)).clamp(1.0, 5.0);
      _transformController.value = Matrix4.diagonal3Values(scale, scale, 1.0);
      _zoomedToWidth = true;
    }
  }

  // ── Builders ──────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return widget.mode == ReadingMode.scroll
        ? _buildScrollMode()
        : _buildPageMode();
  }

  Widget _buildScrollMode() {
    final urls = widget.reversePages
        ? widget.pageUrls.reversed.toList()
        : widget.pageUrls;
    return ListView.builder(
      controller: _scrollController,
      itemCount: urls.length,
      itemBuilder: (context, i) => CachedNetworkImage(
        imageUrl: urls[i],
        fit: BoxFit.fitWidth,
        width: double.infinity,
        placeholder: (_, _) => const AspectRatio(
          aspectRatio: 0.67,
          child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
        ),
        errorWidget: (_, _, _) => const AspectRatio(
          aspectRatio: 0.67,
          child: Icon(Icons.broken_image, color: Colors.white24, size: 48),
        ),
      ),
    );
  }

  Widget _buildPageMode() {
    return PageView.builder(
      controller: _pageController,
      reverse: widget.reversePages,
      itemCount: widget.pageUrls.length,
      onPageChanged: (p) {
        resetZoom();
        widget.onPageChanged(p);
      },
      itemBuilder: (context, i) => LayoutBuilder(
        builder: (context, constraints) {
          _pageConstraints = constraints;
          return InteractiveViewer(
            transformationController: _transformController,
            minScale: 0.5,
            maxScale: 5.0,
            child: CachedNetworkImage(
              imageUrl: widget.pageUrls[i],
              fit: BoxFit.contain,
              placeholder: (_, _) => const Center(
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              errorWidget: (_, _, _) => const Center(
                child: Icon(Icons.broken_image, color: Colors.white24, size: 64),
              ),
            ),
          );
        },
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Local CBZ reader (raw image bytes from device)
// ─────────────────────────────────────────────────────────────────────────────

class LocalComicPageView extends StatefulWidget {
  final String filePath;
  final LocalCbzService localCbz;
  final int pageCount;
  final ReadingMode mode;
  final bool reversePages;
  final int initialPage;
  final ValueChanged<int> onPageChanged;

  const LocalComicPageView({
    super.key,
    required this.filePath,
    required this.localCbz,
    required this.pageCount,
    required this.mode,
    required this.reversePages,
    required this.initialPage,
    required this.onPageChanged,
  });

  @override
  State<LocalComicPageView> createState() => LocalComicPageViewState();
}

class LocalComicPageViewState extends State<LocalComicPageView> {
  late PageController _pageController;
  late ScrollController _scrollController;
  late TransformationController _transformController;

  bool _zoomedToWidth = false;
  BoxConstraints? _pageConstraints;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: widget.initialPage);
    _scrollController = ScrollController();
    _transformController = TransformationController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _scrollController.dispose();
    _transformController.dispose();
    super.dispose();
  }

  // ── Public API ────────────────────────────────────────────────────────────

  // See ComicPageViewState.nextPage()/prevPage() — same scroll-mode handling.
  void nextPage() {
    if (widget.mode == ReadingMode.scroll) {
      _scrollByViewport(1);
      return;
    }
    _pageController.nextPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void prevPage() {
    if (widget.mode == ReadingMode.scroll) {
      _scrollByViewport(-1);
      return;
    }
    _pageController.previousPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void _scrollByViewport(int direction) {
    if (!_scrollController.hasClients) return;
    final position = _scrollController.position;
    final target = (position.pixels + direction * position.viewportDimension * 0.9)
        .clamp(position.minScrollExtent, position.maxScrollExtent);
    _scrollController.animateTo(
      target,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void jumpToPage(int page) {
    resetZoom();
    _pageController.jumpToPage(page);
  }

  void resetZoom() {
    _transformController.value = Matrix4.identity();
    _zoomedToWidth = false;
  }

  void toggleZoom() {
    final c = _pageConstraints;
    if (c == null) return;

    if (_zoomedToWidth) {
      _transformController.value = Matrix4.identity();
      _zoomedToWidth = false;
    } else {
      final scale = (3 * c.maxWidth / (2 * c.maxHeight)).clamp(1.0, 5.0);
      _transformController.value = Matrix4.diagonal3Values(scale, scale, 1.0);
      _zoomedToWidth = true;
    }
  }

  // ── Builders ──────────────────────────────────────────────────────────────

  // Reads each page's bytes on demand rather than holding the whole issue's
  // worth of decoded images at once — see reader_screen.dart's
  // LocalReaderScreen._load() for why (BUG-020, archive/bugs-fixed-archive.md).
  Uint8List _pageAt(int index) => widget.localCbz.readPage(widget.filePath, index);

  // Flutter decodes Image.memory at the source image's full native
  // resolution by default. Local CBZ scans can run well past the device's
  // own display resolution (e.g. this fix was written against a 1988x3056px
  // scan — a ~24MB raw bitmap per page once decoded), and holding several of
  // those at once was part of what pushed a large issue over this tablet's
  // available RAM (BUG-020). Capping cacheWidth to the device's own physical
  // pixel width decodes directly at a size that's actually useful for
  // unzoomed viewing — never smaller than the screen, so no loss of
  // sharpness in the common case, but never wastefully larger than the
  // screen either.
  int _cacheWidth(BuildContext context) {
    final physicalWidth = MediaQuery.sizeOf(context).width * MediaQuery.devicePixelRatioOf(context);
    return physicalWidth.round();
  }

  @override
  Widget build(BuildContext context) {
    final cacheWidth = _cacheWidth(context);

    if (widget.mode == ReadingMode.scroll) {
      return ListView.builder(
        controller: _scrollController,
        itemCount: widget.pageCount,
        itemBuilder: (context, i) {
          final index = widget.reversePages ? widget.pageCount - 1 - i : i;
          return Image.memory(
            _pageAt(index),
            fit: BoxFit.fitWidth,
            width: double.infinity,
            cacheWidth: cacheWidth,
          );
        },
      );
    }

    return PageView.builder(
      controller: _pageController,
      reverse: widget.reversePages,
      itemCount: widget.pageCount,
      onPageChanged: (p) {
        resetZoom();
        widget.onPageChanged(p);
      },
      itemBuilder: (context, i) => LayoutBuilder(
        builder: (context, constraints) {
          _pageConstraints = constraints;
          return InteractiveViewer(
            transformationController: _transformController,
            minScale: 0.5,
            maxScale: 5.0,
            child: Image.memory(_pageAt(i), fit: BoxFit.contain, cacheWidth: cacheWidth),
          );
        },
      ),
    );
  }
}
