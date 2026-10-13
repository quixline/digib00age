// Shared CTA pair reused by the Welcome screen and the empty-library notice —
// both paths into "there's nothing to show yet" lead through the same two
// existing flows, so the actions themselves live in one place.
import 'dart:io';
import 'package:flutter/material.dart';
import '../theme/tokens.dart';

class ConnectOrBrowseActions extends StatelessWidget {
  final VoidCallback? onConnect;
  final VoidCallback? onBrowseLocal;
  final bool dense;

  const ConnectOrBrowseActions({
    super.key,
    this.onConnect,
    this.onBrowseLocal,
    this.dense = false,
  });

  bool get _localFilePickingSupported => Platform.isAndroid;

  @override
  Widget build(BuildContext context) {
    final colors = AppColors.of(context);
    final buttons = <Widget>[
      if (onConnect != null)
        FilledButton.icon(
          onPressed: onConnect,
          icon: const Icon(Icons.cloud_outlined, size: 18),
          label: const Text('Connect to a server'),
          style: FilledButton.styleFrom(
            backgroundColor: colors.accent,
            foregroundColor: colors.onAccent,
            padding: EdgeInsets.symmetric(horizontal: 15, vertical: dense ? 10 : 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusMd)),
          ),
        ),
      if (onBrowseLocal != null && _localFilePickingSupported)
        OutlinedButton.icon(
          onPressed: onBrowseLocal,
          icon: const Icon(Icons.folder_open, size: 18),
          label: const Text('Browse local files'),
          style: OutlinedButton.styleFrom(
            foregroundColor: colors.textPrimary,
            side: BorderSide(color: colors.border),
            padding: EdgeInsets.symmetric(horizontal: 15, vertical: dense ? 10 : 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusMd)),
          ),
        ),
    ];

    if (dense) {
      return Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: buttons);
    }
    return Column(
      children: [
        for (final b in buttons) ...[b, const SizedBox(height: 10)],
      ],
    );
  }
}
