// Shown in place of a blank screen wherever the library is genuinely empty
// (OfflineLibraryView with nothing downloaded/no recent files, HomeScreen
// with no issues yet) — same explainer as WelcomeScreen, without the
// first-launch dismiss control.
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/tokens.dart';
import 'connect_or_browse_actions.dart';

class EmptyLibraryNotice extends StatelessWidget {
  final String message;
  final VoidCallback? onConnect;
  final VoidCallback? onBrowseLocal;

  const EmptyLibraryNotice({
    super.key,
    required this.message,
    this.onConnect,
    this.onBrowseLocal,
  });

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final text = AppText.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Wrap(
            spacing: 6,
            alignment: WrapAlignment.center,
            children: [
              _Chip(colors: colors, icon: Icons.tablet_mac, label: 'Best on tablet'),
              _Chip(colors: colors, icon: Icons.block, label: '100% advert-free'),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'Nothing here yet',
            textAlign: TextAlign.center,
            style: GoogleFonts.bigShouldersDisplay(
              textStyle: text.titleMedium(),
              fontWeight: FontWeight.w800,
              fontSize: 24,
              letterSpacing: 0,
            ).copyWith(color: colors.textPrimary),
          ),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: text.secondary(size: 13),
          ),
          const SizedBox(height: 16),
          ConnectOrBrowseActions(onConnect: onConnect, onBrowseLocal: onBrowseLocal, dense: true),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final AppColors colors;
  final IconData icon;
  final String label;
  const _Chip({required this.colors, required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: colors.surfaceCard,
        border: Border.all(color: colors.border),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: colors.accent),
          const SizedBox(width: 4),
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.4,
              color: colors.accent,
            ),
          ),
        ],
      ),
    );
  }
}
