import 'package:flutter/material.dart';
import '../theme/tokens.dart';

// Numbered page bar (Prev/Next + page numbers, ellipsis-windowed for many
// pages) — mirrors frontend/js/app.js's pageWindow()/renderPaginationControls()
// look and behavior, for the mobile library/custom-library browse pages.
class PaginationBar extends StatelessWidget {
  final int currentPage;
  final int totalPages;
  final ValueChanged<int> onPageChanged;

  const PaginationBar({
    super.key,
    required this.currentPage,
    required this.totalPages,
    required this.onPageChanged,
  });

  static List<int> pageWindow(int current, int total) {
    if (total <= 7) return List.generate(total, (i) => i + 1);
    final pages = <int>{1, total};
    for (var i = (current - 2).clamp(1, total); i <= (current + 2).clamp(1, total); i++) {
      pages.add(i);
    }
    final sorted = pages.toList()..sort();
    return sorted;
  }

  @override
  Widget build(BuildContext context) {
    if (totalPages <= 1) return const SizedBox.shrink();

    final children = <Widget>[
      _PageButton(
        label: '‹',
        onTap: currentPage > 1 ? () => onPageChanged(currentPage - 1) : null,
      ),
    ];

    int? prev;
    for (final p in pageWindow(currentPage, totalPages)) {
      if (prev != null && p - prev > 1) {
        children.add(const Padding(
          padding: EdgeInsets.symmetric(horizontal: 4),
          child: Text('…'),
        ));
      }
      children.add(_PageButton(
        label: '$p',
        current: p == currentPage,
        onTap: p == currentPage ? null : () => onPageChanged(p),
      ));
      prev = p;
    }

    children.add(_PageButton(
      label: '›',
      onTap: currentPage < totalPages ? () => onPageChanged(currentPage + 1) : null,
    ));

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (final w in children) Padding(padding: const EdgeInsets.symmetric(horizontal: 3), child: w),
          ],
        ),
      ),
    );
  }
}

class _PageButton extends StatelessWidget {
  final String label;
  final bool current;
  final VoidCallback? onTap;

  const _PageButton({required this.label, this.current = false, this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final disabled = onTap == null && !current;
    return Material(
      color: current ? colors.surfaceRaised : Colors.transparent,
      borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
        onTap: onTap,
        child: Container(
          width: 36,
          height: 36,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            border: Border.all(color: colors.border),
            borderRadius: BorderRadius.circular(AppSpacing.radiusMd),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: disabled
                  ? colors.textMuted.withValues(alpha: 0.4)
                  : (current ? colors.textPrimary : colors.textMuted),
              fontSize: 13,
              fontWeight: current ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ),
      ),
    );
  }
}
