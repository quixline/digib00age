// Shown in place of a blank screen wherever the library is genuinely empty
// (OfflineLibraryView with nothing downloaded/no recent files, HomeScreen
// with no issues yet) — same explainer as WelcomeScreen, without the
// first-launch dismiss control.
import 'package:flutter/material.dart';
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
          _BuiltForTabletsChip(colors: colors),
          const SizedBox(height: 10),
          Text(
            'Nothing here yet',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: 'BigShouldersDisplay',
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

class _BuiltForTabletsChip extends StatelessWidget {
  final AppColors colors;
  const _BuiltForTabletsChip({required this.colors});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 6),
      decoration: BoxDecoration(
        color: colors.surfaceCard,
        border: Border.all(color: colors.border),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: colors.accent, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(
            'BUILT FOR TABLETS',
            style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, letterSpacing: 0.6, color: colors.accent),
          ),
        ],
      ),
    );
  }
}
