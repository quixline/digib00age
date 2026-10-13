// First-launch interstitial (route '/welcome') — also reachable any time
// afterwards via Settings > "What is this app?". Explains what digib00age is
// and routes into the two existing entry flows (server settings, local file
// picker) rather than introducing new ones.
import 'package:flutter/material.dart';
import '../services/settings_service.dart';
import '../services/local_cbz_service.dart';
import '../theme/tokens.dart';
import '../widgets/connect_or_browse_actions.dart';
import 'reader_screen.dart' show LocalReaderArgs;

class WelcomeScreen extends StatefulWidget {
  final SettingsService settings;
  final LocalCbzService localCbz;

  const WelcomeScreen({super.key, required this.settings, required this.localCbz});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> {
  late bool _dontShowAgain;

  @override
  void initState() {
    super.initState();
    _dontShowAgain = widget.settings.suppressWelcome;
  }

  void _finish() {
    widget.settings.suppressWelcome = _dontShowAgain;
    if (!mounted) return;
    if (Navigator.of(context).canPop()) {
      Navigator.of(context).pop();
    } else {
      Navigator.of(context).pushReplacementNamed('/');
    }
  }

  Future<void> _goConnect() async {
    await Navigator.of(context).pushNamed('/settings');
    if (!mounted) return;
    _finish();
  }

  Future<void> _goLocal() async {
    final path = await widget.localCbz.pickFile();
    if (path == null || !mounted) return;
    widget.settings.addRecentLocalFile(path);
    _finish();
    if (!mounted) return;
    Navigator.of(context).pushNamed('/reader/local', arguments: LocalReaderArgs(path));
  }

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final text = AppText.of(context);
    final canClose = Navigator.of(context).canPop();

    return Scaffold(
      backgroundColor: colors.canvas,
      body: SafeArea(
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(28, 24, 28, 20),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 360),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                  const SizedBox(height: 24),
                  Image.asset(
                    Theme.of(context).brightness == Brightness.light
                        ? 'assets/logo/lockup-dark.png'
                        : 'assets/logo/lockup-light.png',
                    height: 28,
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Your comics,\nat home or on the go',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontFamily: 'BigShouldersDisplay',
                      fontWeight: FontWeight.w800,
                      fontSize: 32,
                      height: 1.05,
                      letterSpacing: 0,
                    ).copyWith(color: colors.textPrimary),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Connect to your own digib00age server, or open CBZ files '
                    'straight from this device — no account, no cloud required.',
                    textAlign: TextAlign.center,
                    style: text.secondary(size: 14),
                  ),
                  const SizedBox(height: 20),
                  _FeatureCard(colors: colors),
                  const SizedBox(height: 28),
                  ConnectOrBrowseActions(onConnect: _goConnect, onBrowseLocal: _goLocal),
                  const SizedBox(height: 14),
                  InkWell(
                    onTap: () => setState(() => _dontShowAgain = !_dontShowAgain),
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Checkbox(
                            value: _dontShowAgain,
                            visualDensity: VisualDensity.compact,
                            onChanged: (v) => setState(() => _dontShowAgain = v ?? false),
                          ),
                          Text("Don't show this again", style: text.meta(size: 12)),
                        ],
                      ),
                    ),
                  ),
                    ],
                  ),
                ),
              ),
            ),
            if (canClose)
              Positioned(
                top: 4,
                right: 8,
                child: IconButton(
                  icon: Icon(Icons.close, color: colors.textSecondary),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final AppColors colors;
  const _FeatureCard({required this.colors});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 15),
      decoration: BoxDecoration(
        color: colors.surfaceCard,
        border: Border.all(color: colors.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(color: colors.accent, shape: BoxShape.circle),
              ),
              const SizedBox(width: 7),
              Text(
                'BUILT FOR TABLETS',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 1, color: colors.accent),
              ),
            ],
          ),
          const SizedBox(height: 11),
          _FeatureBullet(
            colors: colors,
            bold: 'Reading progress syncs',
            rest: ' between server and device, with a visible "last synced" indicator',
          ),
          const SizedBox(height: 9),
          _FeatureBullet(
            colors: colors,
            bold: 'Download issues',
            rest: ' for offline reading — no connection needed',
          ),
          const SizedBox(height: 9),
          _FeatureBullet(
            colors: colors,
            bold: 'Scroll or page',
            rest: ' reading modes, with manga right-to-left support',
          ),
        ],
      ),
    );
  }
}

class _FeatureBullet extends StatelessWidget {
  final AppColors colors;
  final String bold;
  final String rest;
  const _FeatureBullet({required this.colors, required this.bold, required this.rest});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 2),
          child: Icon(Icons.check, size: 14, color: colors.accent),
        ),
        const SizedBox(width: 9),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: TextStyle(fontSize: 12.5, height: 1.45, color: colors.textSecondary),
              children: [
                TextSpan(text: bold, style: TextStyle(fontWeight: FontWeight.w700, color: colors.textPrimary)),
                TextSpan(text: rest),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
