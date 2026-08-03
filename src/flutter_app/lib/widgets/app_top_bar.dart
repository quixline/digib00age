// Shared header (logo + search + settings) — shown on both Home and Browse
// per the design prototype (Flutter App Redesign.dc.html screenPIsHome /
// screenPIsBrowse both include this exact block).
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/tokens.dart';
import 'comic_search_delegate.dart';

class AppTopBar extends StatelessWidget {
  final ApiService api;
  final VoidCallback onSettingsReturn;

  const AppTopBar({super.key, required this.api, required this.onSettingsReturn});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.of(context).border)),
      ),
      child: Row(
        children: [
          Image.asset(
            Theme.of(context).brightness == Brightness.light
                ? 'assets/logo/lockup-dark.png'
                : 'assets/logo/lockup-light.png',
            height: 24,
          ),
          const Spacer(),
          _RoundIconButton(
            glyph: '⌕',
            onTap: () => showSearch(context: context, delegate: ComicSearchDelegate(api: api)),
          ),
          const SizedBox(width: 10),
          _RoundIconButton(
            glyph: '⚙',
            onTap: () async {
              await Navigator.of(context, rootNavigator: true).pushNamed('/settings');
              onSettingsReturn();
            },
          ),
        ],
      ),
    );
  }
}

class _RoundIconButton extends StatelessWidget {
  final String glyph;
  final VoidCallback onTap;
  const _RoundIconButton({required this.glyph, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 38,
      height: 38,
      child: Material(
        color: Colors.transparent,
        shape: const CircleBorder(),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onTap,
          child: Center(
            child: Text(glyph, style: TextStyle(color: AppColors.of(context).textSecondary, fontSize: 18)),
          ),
        ),
      ),
    );
  }
}
