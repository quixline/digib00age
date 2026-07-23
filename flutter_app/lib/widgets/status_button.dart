// Circular ○ unread / ◐ reading / ✓ read button. Tapping toggles between
// read and unread (mirrors frontend/js/app.js's status button — "reading" is
// only ever reached by actually turning pages, never by manual toggle).
import 'package:flutter/material.dart';
import '../theme/tokens.dart';

class StatusButton extends StatelessWidget {
  final String status; // 'unread' | 'reading' | 'read'
  final double size;
  final VoidCallback onTap;

  const StatusButton({
    super.key,
    required this.status,
    required this.onTap,
    this.size = 28,
  });

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final Color color;
    final String glyph;
    switch (status) {
      case 'read':
        color = colors.readGreen;
        glyph = '✓';
        break;
      case 'reading':
        color = colors.stateReadingBlue;
        glyph = '◐';
        break;
      default:
        color = colors.textMuted;
        glyph = '○';
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: color, width: 1.4),
        ),
        child: Text(
          glyph,
          style: TextStyle(color: color, fontSize: size * 0.5, height: 1),
        ),
      ),
    );
  }
}
