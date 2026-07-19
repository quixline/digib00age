import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';
import 'package:screen_retriever/screen_retriever.dart';
import 'package:window_manager/window_manager.dart';

// Resizes the Windows desktop reader window to match the comic being opened,
// so the window's shape roughly matches its cover instead of staying at a
// fixed size for every comic. Windows-only — Android/iOS keep their normal
// fixed-to-device-screen behavior; callers don't need their own Platform
// check.
class WindowResizeService {
  static const _fraction = 0.75;

  // Guards against out-of-order completion: comics are opened/navigated
  // faster than a resize (network fetch + decode) can complete, so an older
  // request finishing after a newer one would otherwise silently overwrite
  // the newer comic's correct size with its own stale one. Only the request
  // that's still the latest when it finishes is allowed to actually resize.
  static int _requestSeq = 0;

  // Decodes the cover's pixel dimensions and resizes+centers the window to
  // 75% of that (capped to fit the primary display, preserving aspect
  // ratio). dart:ui only exposes width/height on a decoded frame (not on the
  // codec itself), so this does decode page 0's pixels — just the one page,
  // not the whole comic. Best-effort: any failure here (bad bytes, plugin
  // not ready, etc.) is swallowed rather than surfaced — this is UX polish
  // and must never block or break opening a comic.
  //
  // `context` must still be mounted when called — used (synchronously, no
  // await in between) to measure how much of the current window rect is OS
  // chrome (title bar/borders) rather than actual page-display area, since
  // window_manager's setSize/getSize both operate on the outer window rect,
  // not the content area. Without correcting for that, a short window (wide/
  // landscape cover) loses a much bigger fraction of its height budget to
  // the title bar than a tall one does, visibly cropping the page.
  static Future<void> resizeForCoverBytes(Uint8List bytes, BuildContext context) async {
    if (!Platform.isWindows) return;
    final requestId = ++_requestSeq;
    try {
      if (!context.mounted) return;
      final contentSize = MediaQuery.sizeOf(context);
      final frameSize = await windowManager.getSize();
      final chromeWidth = (frameSize.width - contentSize.width).clamp(0.0, double.infinity);
      final chromeHeight = (frameSize.height - contentSize.height).clamp(0.0, double.infinity);

      final codec = await ui.instantiateImageCodec(bytes);
      final frame = await codec.getNextFrame();
      final coverSize = Size(
        frame.image.width.toDouble(),
        frame.image.height.toDouble(),
      );
      frame.image.dispose();
      codec.dispose();

      final display = await screenRetriever.getPrimaryDisplay();
      final screenSize = display.visibleSize ?? display.size;
      final maxContentSize = Size(
        (screenSize.width - chromeWidth).clamp(1.0, double.infinity),
        (screenSize.height - chromeHeight).clamp(1.0, double.infinity),
      );

      final targetContent = _computeWindowSize(coverSize, maxContentSize);
      final targetFrame = Size(
        targetContent.width + chromeWidth,
        targetContent.height + chromeHeight,
      );

      if (requestId != _requestSeq) return; // superseded by a newer comic's resize
      await windowManager.setSize(targetFrame);
      await windowManager.center();
    } catch (_) {}
  }

  // Pure + testable: 75% of the cover's pixel size, scaled down further
  // (preserving aspect ratio) if that would exceed the given max size.
  static Size _computeWindowSize(Size coverSize, Size maxSize) {
    var target = coverSize * _fraction;
    if (target.width > maxSize.width || target.height > maxSize.height) {
      final scale = [
        maxSize.width / target.width,
        maxSize.height / target.height,
      ].reduce((a, b) => a < b ? a : b);
      target = target * scale;
    }
    return target;
  }
}
