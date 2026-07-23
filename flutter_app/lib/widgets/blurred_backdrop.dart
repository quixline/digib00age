// Series/Issue detail hero backdrop: cover → blur → dark overlay → gradient
// fade to canvas (design_handoff_tablet_app/tokens/elevation.css's
// "series-hero backdrop recipe").
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../theme/tokens.dart';

class BlurredBackdrop extends StatelessWidget {
  final String imageUrl;
  const BlurredBackdrop({super.key, required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        fit: StackFit.expand,
        children: [
          Opacity(
            opacity: 0.28,
            child: ImageFiltered(
              imageFilter: ui.ImageFilter.blur(sigmaX: 4, sigmaY: 4),
              child: CachedNetworkImage(imageUrl: imageUrl, fit: BoxFit.cover, errorWidget: (_, _, _) => const SizedBox()),
            ),
          ),
          Container(color: Colors.black.withValues(alpha: 0.45)),
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Colors.transparent, AppColors.of(context).canvas],
                stops: const [0.3, 1.0],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
