// Persistent left nav rail (design_handoff_tablet_app/README.md §"Nav rail").
// Collapsed 64px / expanded 196px, animates over 180ms.
import 'package:flutter/material.dart';
import '../models/custom_tab.dart';
import '../theme/tokens.dart';

enum NavKind { home, all, singles, series, unread, reading, read, library }

typedef NavTarget = ({NavKind kind, int? tabId});

const homeTarget = (kind: NavKind.home, tabId: null);

class NavRail extends StatelessWidget {
  final bool collapsed;
  final NavTarget active;
  final List<CustomTabInfo> customTabs;
  final VoidCallback onToggle;
  final void Function(NavTarget target) onSelect;

  const NavRail({
    super.key,
    required this.collapsed,
    required this.active,
    required this.customTabs,
    required this.onToggle,
    required this.onSelect,
  });

  bool _isActive(NavKind kind, {int? tabId}) =>
      active.kind == kind && active.tabId == tabId;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: AppMotion.railDuration,
      curve: AppMotion.railCurve,
      width: collapsed ? 64 : 196,
      decoration: const BoxDecoration(
        color: AppColors.surfaceCard,
        border: Border(right: BorderSide(color: AppColors.border, width: 1)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 14),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _ToggleButton(onTap: onToggle),
            const SizedBox(height: 4),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.home),
              icon: Icons.home_outlined,
              label: 'Home',
              onTap: () => onSelect((kind: NavKind.home, tabId: null)),
            ),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.all),
              icon: Icons.grid_view_outlined,
              label: 'All',
              onTap: () => onSelect((kind: NavKind.all, tabId: null)),
            ),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.singles),
              icon: Icons.menu_book_outlined,
              label: 'Singles',
              onTap: () => onSelect((kind: NavKind.singles, tabId: null)),
            ),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.series),
              icon: Icons.layers_outlined,
              label: 'Series',
              onTap: () => onSelect((kind: NavKind.series, tabId: null)),
            ),
            _Divider(collapsed: collapsed),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.unread),
              glyph: '○',
              label: 'Unread',
              onTap: () => onSelect((kind: NavKind.unread, tabId: null)),
            ),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.reading),
              glyph: '◐',
              label: 'Reading',
              onTap: () => onSelect((kind: NavKind.reading, tabId: null)),
            ),
            _Row(
              collapsed: collapsed,
              active: _isActive(NavKind.read),
              glyph: '✓',
              label: 'Read',
              onTap: () => onSelect((kind: NavKind.read, tabId: null)),
            ),
            if (customTabs.isNotEmpty) ...[
              _Divider(collapsed: collapsed),
              if (!collapsed)
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 8, 14, 4),
                  child: Text('Libraries', style: AppText.eyebrow()),
                ),
              for (final tab in customTabs)
                _LibraryRow(
                  collapsed: collapsed,
                  active: _isActive(NavKind.library, tabId: tab.id),
                  tab: tab,
                  onTap: () => onSelect((kind: NavKind.library, tabId: tab.id)),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ToggleButton extends StatelessWidget {
  final VoidCallback onTap;
  const _ToggleButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 36,
      child: IconButton(
        onPressed: onTap,
        icon: const Icon(Icons.view_sidebar_outlined, size: 18, color: AppColors.textMuted),
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  final bool collapsed;
  const _Divider({required this.collapsed});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 1,
      margin: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
      color: AppColors.border,
    );
  }
}

class _Row extends StatelessWidget {
  final bool collapsed;
  final bool active;
  final IconData? icon;
  final String? glyph;
  final String label;
  final VoidCallback onTap;

  const _Row({
    required this.collapsed,
    required this.active,
    this.icon,
    this.glyph,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final fg = active ? AppColors.accent : AppColors.textSecondary;
    final iconWidget = icon != null
        ? Icon(icon, size: 19, color: fg)
        : SizedBox(
            width: 19,
            child: Text(glyph!, textAlign: TextAlign.center, style: TextStyle(color: fg, fontSize: 15, height: 1)),
          );

    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Material(
        color: active ? AppColors.accentTint : Colors.transparent,
        borderRadius: BorderRadius.circular(6),
        child: InkWell(
          borderRadius: BorderRadius.circular(6),
          onTap: onTap,
          child: Padding(
            padding: collapsed
                ? const EdgeInsets.symmetric(vertical: 10)
                : const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: collapsed
                ? Center(child: iconWidget)
                : Row(
                    children: [
                      iconWidget,
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          label,
                          style: AppText.label(size: 14, weight: FontWeight.w600, color: fg),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}

class _LibraryRow extends StatelessWidget {
  final bool collapsed;
  final bool active;
  final CustomTabInfo tab;
  final VoidCallback onTap;

  const _LibraryRow({
    required this.collapsed,
    required this.active,
    required this.tab,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Material(
        color: active ? AppColors.accentTint : Colors.transparent,
        borderRadius: BorderRadius.circular(6),
        child: InkWell(
          borderRadius: BorderRadius.circular(6),
          onTap: onTap,
          child: Padding(
            padding: collapsed
                ? const EdgeInsets.symmetric(vertical: 8)
                : const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: collapsed
                ? Center(
                    child: Container(
                      width: 30,
                      height: 30,
                      alignment: Alignment.center,
                      decoration: active
                          ? BoxDecoration(shape: BoxShape.circle, border: Border.all(color: AppColors.accent, width: 2))
                          : null,
                      child: Container(
                        width: 26,
                        height: 26,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(color: AppColors.accent, shape: BoxShape.circle),
                        child: Text(
                          tab.firstLetterGlyph,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                      ),
                    ),
                  )
                : Text(
                    tab.name,
                    style: AppText.label(
                      size: 14,
                      weight: FontWeight.w600,
                      color: active ? AppColors.accent : AppColors.textSecondary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
          ),
        ),
      ),
    );
  }
}
