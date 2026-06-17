import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

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

  void nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void prevPage() {
    _pageController.previousPage(
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
  final List<Uint8List> pages;
  final ReadingMode mode;
  final bool reversePages;
  final int initialPage;
  final ValueChanged<int> onPageChanged;

  const LocalComicPageView({
    super.key,
    required this.pages,
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
  late TransformationController _transformController;

  bool _zoomedToWidth = false;
  BoxConstraints? _pageConstraints;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: widget.initialPage);
    _transformController = TransformationController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _transformController.dispose();
    super.dispose();
  }

  // ── Public API ────────────────────────────────────────────────────────────

  void nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  void prevPage() {
    _pageController.previousPage(
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

  @override
  Widget build(BuildContext context) {
    if (widget.mode == ReadingMode.scroll) {
      final pages = widget.reversePages
          ? widget.pages.reversed.toList()
          : widget.pages;
      return ListView.builder(
        itemCount: pages.length,
        itemBuilder: (context, i) => Image.memory(
          pages[i],
          fit: BoxFit.fitWidth,
          width: double.infinity,
        ),
      );
    }

    return PageView.builder(
      controller: _pageController,
      reverse: widget.reversePages,
      itemCount: widget.pages.length,
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
            child: Image.memory(widget.pages[i], fit: BoxFit.contain),
          );
        },
      ),
    );
  }
}
