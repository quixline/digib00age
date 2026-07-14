import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'comic_page_view.dart';

class ToolbarOverlay extends StatefulWidget {
  final Widget child;
  final Widget topBar;
  final Widget bottomBar;
  final ReadingMode mode;
  final VoidCallback? onPrevPage;
  final VoidCallback? onNextPage;
  final VoidCallback? onDoubleTapMiddle;
  final VoidCallback? onBack;
  final bool startVisible;

  const ToolbarOverlay({
    super.key,
    required this.child,
    required this.topBar,
    required this.bottomBar,
    required this.mode,
    this.onPrevPage,
    this.onNextPage,
    this.onDoubleTapMiddle,
    this.onBack,
    this.startVisible = true,
  });

  @override
  State<ToolbarOverlay> createState() => _ToolbarOverlayState();
}

class _ToolbarOverlayState extends State<ToolbarOverlay>
    with TickerProviderStateMixin {
  // Toolbar fade
  late AnimationController _toolbarAnim;
  late Animation<double> _toolbarFade;
  Timer? _hideTimer;
  bool _visible = true;

  // Arrow flash — fast in, slow out
  late AnimationController _arrowAnim;
  late Animation<double> _arrowFade;
  Timer? _arrowTimer;

  @override
  void initState() {
    super.initState();
    _visible = widget.startVisible;

    _toolbarAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 250),
      value: widget.startVisible ? 1.0 : 0.0,
    );
    _toolbarFade = CurvedAnimation(parent: _toolbarAnim, curve: Curves.easeInOut);
    if (_visible) _scheduleHide();

    _arrowAnim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
    );
    _arrowFade = CurvedAnimation(parent: _arrowAnim, curve: Curves.easeOut);
  }

  @override
  void dispose() {
    _hideTimer?.cancel();
    _arrowTimer?.cancel();
    _toolbarAnim.dispose();
    _arrowAnim.dispose();
    super.dispose();
  }

  void _scheduleHide() {
    _hideTimer?.cancel();
    _hideTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) _hide();
    });
  }

  void _show() {
    setState(() => _visible = true);
    _toolbarAnim.forward();
    _scheduleHide();
  }

  void _hide() {
    setState(() => _visible = false);
    _toolbarAnim.reverse();
  }

  void _toggle() => _visible ? _hide() : _show();

  void _flashArrows() {
    _arrowAnim.forward(from: 0.0);
    _arrowTimer?.cancel();
    _arrowTimer = Timer(const Duration(milliseconds: 1100), () {
      if (mounted) _arrowAnim.reverse();
    });
  }

  void _onTapLeft() {
    widget.onPrevPage?.call();
    _flashArrows();
  }

  void _onTapRight() {
    widget.onNextPage?.call();
    _flashArrows();
  }

  void _onTapMiddle() {
    _toggle();
    _flashArrows();
  }

  // Desktop/keyboard parity for the touch-only tap zones below — mouse users
  // get the existing tap zones, keyboard-only users get arrow keys + Escape.
  KeyEventResult _onKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    switch (event.logicalKey) {
      case LogicalKeyboardKey.arrowLeft:
      case LogicalKeyboardKey.arrowUp:
        widget.onPrevPage?.call();
        return KeyEventResult.handled;
      case LogicalKeyboardKey.arrowRight:
      case LogicalKeyboardKey.arrowDown:
        widget.onNextPage?.call();
        return KeyEventResult.handled;
      case LogicalKeyboardKey.escape:
        widget.onBack?.call();
        return KeyEventResult.handled;
      default:
        return KeyEventResult.ignored;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPage = widget.mode == ReadingMode.page;

    return Focus(
      autofocus: true,
      onKeyEvent: _onKeyEvent,
      child: Stack(
      children: [
        widget.child,

        // ── Tap zones ────────────────────────────────────────────────────────
        if (isPage)
          // Page mode: 25% left / 50% middle / 25% right
          Positioned.fill(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  flex: 25,
                  child: GestureDetector(
                    behavior: HitTestBehavior.translucent,
                    onTap: _onTapLeft,
                  ),
                ),
                Expanded(
                  flex: 50,
                  child: GestureDetector(
                    behavior: HitTestBehavior.translucent,
                    onTap: _onTapMiddle,
                    onDoubleTap: widget.onDoubleTapMiddle,
                  ),
                ),
                Expanded(
                  flex: 25,
                  child: GestureDetector(
                    behavior: HitTestBehavior.translucent,
                    onTap: _onTapRight,
                  ),
                ),
              ],
            ),
          )
        else
          // Scroll mode: whole screen tap toggles toolbar
          Positioned.fill(
            child: GestureDetector(
              behavior: HitTestBehavior.translucent,
              onTap: _onTapMiddle,
            ),
          ),

        // ── Arrow hints (visual only, not tappable) ───────────────────────
        if (isPage) ...[
          // Left chevron
          Positioned(
            left: 12,
            top: 0,
            bottom: 0,
            child: IgnorePointer(
              child: FadeTransition(
                opacity: _arrowFade,
                child: const Center(
                  child: Icon(Icons.chevron_left, color: Colors.white60, size: 56),
                ),
              ),
            ),
          ),
          // Right chevron
          Positioned(
            right: 12,
            top: 0,
            bottom: 0,
            child: IgnorePointer(
              child: FadeTransition(
                opacity: _arrowFade,
                child: const Center(
                  child: Icon(Icons.chevron_right, color: Colors.white60, size: 56),
                ),
              ),
            ),
          ),
        ] else ...[
          // Up arrow
          Positioned(
            top: 80,
            left: 0,
            right: 0,
            child: IgnorePointer(
              child: FadeTransition(
                opacity: _arrowFade,
                child: const Center(
                  child: Icon(Icons.keyboard_arrow_up, color: Colors.white60, size: 48),
                ),
              ),
            ),
          ),
          // Down arrow
          Positioned(
            bottom: 80,
            left: 0,
            right: 0,
            child: IgnorePointer(
              child: FadeTransition(
                opacity: _arrowFade,
                child: const Center(
                  child: Icon(Icons.keyboard_arrow_down, color: Colors.white60, size: 48),
                ),
              ),
            ),
          ),
        ],

        // ── Toolbar bars ──────────────────────────────────────────────────
        Positioned(
          top: 0, left: 0, right: 0,
          child: FadeTransition(
            opacity: _toolbarFade,
            child: IgnorePointer(
              ignoring: !_visible,
              child: widget.topBar,
            ),
          ),
        ),
        Positioned(
          bottom: 0, left: 0, right: 0,
          child: FadeTransition(
            opacity: _toolbarFade,
            child: IgnorePointer(
              ignoring: !_visible,
              child: widget.bottomBar,
            ),
          ),
        ),
      ],
      ),
    );
  }
}
