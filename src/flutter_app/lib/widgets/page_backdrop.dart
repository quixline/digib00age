// Soft, static tinted glow blobs behind the library grid — gives the page a
// little depth. Deliberately not a blurred-photo backdrop (tried porting the
// web's `.page-bg` cover-blur effect directly; ImageFiltered+ShaderMask
// composited into hard-edged patches on device, likely an Impeller quirk).
// Native RadialGradient decorations render identically everywhere and can't
// produce a hard edge — the gradient itself is the fade.
import 'package:flutter/material.dart';
import '../theme/tokens.dart';

class PageBackdrop extends StatelessWidget {
  const PageBackdrop({super.key});

  static const _blobs = [
    (x: 0.12, y: 0.15, s: 1.0),
    (x: 0.88, y: 0.10, s: 0.85),
    (x: 0.20, y: 0.88, s: 1.1),
    (x: 0.85, y: 0.82, s: 0.95),
  ];

  static Color _invert(Color c) => Color.fromARGB(
        255,
        255 - (c.r * 255).round(),
        255 - (c.g * 255).round(),
        255 - (c.b * 255).round(),
      );

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final isLight = Theme.of(context).brightness == Brightness.light;
    final base = [colors.accent, colors.readGreen, colors.favouriteGold, colors.accent];
    final tints = isLight ? base.map(_invert).toList() : base;

    return IgnorePointer(
      child: ClipRect(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return Stack(
              children: List.generate(_blobs.length, (i) {
                final b = _blobs[i];
                final size = constraints.maxWidth * 0.55 * b.s;
                return Positioned(
                  left: constraints.maxWidth * b.x - size / 2,
                  top: constraints.maxHeight * b.y - size / 2,
                  width: size,
                  height: size,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          tints[i % tints.length].withValues(alpha: colors.pagebgBlobOpacity),
                          tints[i % tints.length].withValues(alpha: 0),
                        ],
                      ),
                    ),
                  ),
                );
              }),
            );
          },
        ),
      ),
    );
  }
}
