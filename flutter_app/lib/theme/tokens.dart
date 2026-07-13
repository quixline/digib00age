// digib00age design tokens — dark theme only (design_handoff_tablet_app/tokens/*.css).
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  AppColors._();

  static const canvas = Color(0xFF0D0E10);
  static const surfaceCard = Color(0xFF16181C);
  static const surfaceRaised = Color(0xFF1F2228);
  static const surfaceSunken = Color(0xFF2A2E36);
  static const border = Color(0xFF2C3038);
  static const borderStrong = Color(0xFF3A3F49);

  static const textPrimary = Color(0xFFF2F4F7);
  static const textSecondary = Color(0xFF9BA1AC);
  static const textMuted = Color(0xFF5E6470);

  static const accent = Color(0xFF0A5FFF);
  static const accentHover = Color(0xFF2E72FF);
  static const accentPress = Color(0xFF0048D6);
  static Color get accentTint => accent.withValues(alpha: 0.16);
  static const onAccent = Colors.white;

  static const readGreen = Color(0xFF3FB877);
  static const stateReadingBlue = accent;
  static const favouriteGold = Color(0xFFF0C419);
}

class AppSpacing {
  AppSpacing._();

  static const radiusXs = 3.0;
  static const radiusSm = 6.0;
  static const radiusMd = 8.0;
  static const radiusLg = 10.0;
  static const radiusPill = 999.0;

  static const cardMin = 150.0;
  static const cardGap = 14.0;
  static const coverRatio = 2 / 3;
}

class AppMotion {
  AppMotion._();

  static const railDuration = Duration(milliseconds: 180);
  static const railCurve = Cubic(0.4, 0, 0.2, 1);
  static const lift = 3.0;
}

class AppText {
  AppText._();

  static TextStyle _base({
    required double size,
    required FontWeight weight,
    double? letterSpacing,
    double? height,
    Color color = AppColors.textPrimary,
  }) {
    return GoogleFonts.hankenGrotesk(
      fontSize: size,
      fontWeight: weight,
      letterSpacing: letterSpacing,
      height: height,
      color: color,
    );
  }

  static TextStyle eyebrow({Color color = AppColors.textMuted}) => _base(
        size: 11,
        weight: FontWeight.w700,
        letterSpacing: 11 * 0.08,
        color: color,
      );

  static TextStyle titleLarge({Color color = AppColors.textPrimary}) => _base(
        size: 32,
        weight: FontWeight.w800,
        letterSpacing: 32 * -0.02,
        height: 1.1,
        color: color,
      );

  static TextStyle titleMedium({Color color = AppColors.textPrimary}) => _base(
        size: 30,
        weight: FontWeight.w800,
        letterSpacing: 30 * -0.02,
        height: 1.1,
        color: color,
      );

  static TextStyle countBig({Color color = AppColors.accent}) => _base(
        size: 22,
        weight: FontWeight.w800,
        color: color,
      );

  static TextStyle body({Color color = AppColors.textPrimary}) => _base(
        size: 15,
        weight: FontWeight.w400,
        height: 1.7,
        color: color,
      );

  static TextStyle label({
    double size = 14,
    FontWeight weight = FontWeight.w700,
    Color color = AppColors.textPrimary,
  }) =>
      _base(size: size, weight: weight, color: color);

  static TextStyle meta({
    double size = 12,
    Color color = AppColors.textMuted,
  }) =>
      _base(size: size, weight: FontWeight.w400, color: color);

  static TextStyle secondary({
    double size = 14,
    Color color = AppColors.textSecondary,
  }) =>
      _base(size: size, weight: FontWeight.w400, color: color);
}

ThemeData buildAppTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.accent,
      brightness: Brightness.dark,
      primary: AppColors.accent,
      surface: AppColors.surfaceCard,
    ),
    scaffoldBackgroundColor: AppColors.canvas,
    cardColor: AppColors.surfaceCard,
    dividerColor: AppColors.border,
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.surfaceCard,
      elevation: 0,
      centerTitle: false,
    ),
    tabBarTheme: const TabBarThemeData(
      dividerColor: Colors.transparent,
    ),
  );
  return base.copyWith(
    textTheme: GoogleFonts.hankenGroteskTextTheme(base.textTheme).apply(
      bodyColor: AppColors.textPrimary,
      displayColor: AppColors.textPrimary,
    ),
  );
}
