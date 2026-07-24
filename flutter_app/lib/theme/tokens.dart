// digib00age design tokens — light + dark palettes (design_handoff_tablet_app/tokens/*.css).
// Palette values mirror frontend/css/tokens-dark.css and tokens-light.css so the
// mobile reader and web app stay visually aligned.
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

@immutable
class AppColors extends ThemeExtension<AppColors> {
  final Color canvas;
  final Color surfaceCard;
  final Color surfaceRaised;
  final Color surfaceSunken;
  final Color border;
  final Color borderStrong;

  final Color textPrimary;
  final Color textSecondary;
  final Color textMuted;

  final Color accent;
  final Color accentHover;
  final Color accentPress;
  final Color onAccent;

  final Color readGreen;
  final Color favouriteGold;
  final Color cardBorder;

  final double pagebgBlobOpacity;

  const AppColors({
    required this.canvas,
    required this.surfaceCard,
    required this.surfaceRaised,
    required this.surfaceSunken,
    required this.border,
    required this.borderStrong,
    required this.textPrimary,
    required this.textSecondary,
    required this.textMuted,
    required this.accent,
    required this.accentHover,
    required this.accentPress,
    required this.onAccent,
    required this.readGreen,
    required this.favouriteGold,
    required this.cardBorder,
    required this.pagebgBlobOpacity,
  });

  Color get accentTint => accent.withValues(alpha: 0.16);
  Color get stateReadingBlue => accent;

  // frontend/css/tokens-dark.css
  static const dark = AppColors(
    canvas: Color(0xFF0D0E10),
    surfaceCard: Color(0xFF16181C),
    surfaceRaised: Color(0xFF1F2228),
    surfaceSunken: Color(0xFF2A2E36),
    border: Color(0xFF2C3038),
    borderStrong: Color(0xFF3A3F49),
    textPrimary: Color(0xFFF2F4F7),
    textSecondary: Color(0xFF9BA1AC),
    textMuted: Color(0xFF5E6470),
    accent: Color(0xFF0A5FFF),
    accentHover: Color(0xFF2E72FF),
    accentPress: Color(0xFF0048D6),
    onAccent: Colors.white,
    readGreen: Color(0xFF3FB877),
    favouriteGold: Color(0xFFF0C419), // tokens-base.css --favourite, theme-neutral
    cardBorder: Colors.white,
    pagebgBlobOpacity: 0.14,
  );

  // frontend/css/tokens-light.css :root[data-theme="light"]
  static const light = AppColors(
    canvas: Color(0xFFd2edf5),
    surfaceCard: Color(0xFFd8e3ef),
    surfaceRaised: Color(0xFFEDF0F4),
    surfaceSunken: Color(0xFFE1E6EC),
    border: Color(0xFFC8D1DC),
    borderStrong: Color(0xFFAEB9C4),
    textPrimary: Color(0xFF14161A),
    textSecondary: Color(0xFF565C66),
    textMuted: Color(0xFF888E98),
    accent: Color(0xFF0A5FFF),
    accentHover: Color(0xFF0048D6),
    accentPress: Color(0xFF0039AB),
    onAccent: Colors.white,
    readGreen: Color(0xFF2E9E60),
    favouriteGold: Color(0xFFF0C419), // tokens-base.css --favourite, theme-neutral
    cardBorder: Colors.black,
    pagebgBlobOpacity: 0.10,
  );

  static AppColors of(BuildContext context) =>
      Theme.of(context).extension<AppColors>() ?? dark;

  @override
  AppColors copyWith({
    Color? canvas,
    Color? surfaceCard,
    Color? surfaceRaised,
    Color? surfaceSunken,
    Color? border,
    Color? borderStrong,
    Color? textPrimary,
    Color? textSecondary,
    Color? textMuted,
    Color? accent,
    Color? accentHover,
    Color? accentPress,
    Color? onAccent,
    Color? readGreen,
    Color? favouriteGold,
    Color? cardBorder,
    double? pagebgBlobOpacity,
  }) {
    return AppColors(
      canvas: canvas ?? this.canvas,
      surfaceCard: surfaceCard ?? this.surfaceCard,
      surfaceRaised: surfaceRaised ?? this.surfaceRaised,
      surfaceSunken: surfaceSunken ?? this.surfaceSunken,
      border: border ?? this.border,
      borderStrong: borderStrong ?? this.borderStrong,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      textMuted: textMuted ?? this.textMuted,
      accent: accent ?? this.accent,
      accentHover: accentHover ?? this.accentHover,
      accentPress: accentPress ?? this.accentPress,
      onAccent: onAccent ?? this.onAccent,
      readGreen: readGreen ?? this.readGreen,
      favouriteGold: favouriteGold ?? this.favouriteGold,
      cardBorder: cardBorder ?? this.cardBorder,
      pagebgBlobOpacity: pagebgBlobOpacity ?? this.pagebgBlobOpacity,
    );
  }

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      canvas: Color.lerp(canvas, other.canvas, t)!,
      surfaceCard: Color.lerp(surfaceCard, other.surfaceCard, t)!,
      surfaceRaised: Color.lerp(surfaceRaised, other.surfaceRaised, t)!,
      surfaceSunken: Color.lerp(surfaceSunken, other.surfaceSunken, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textMuted: Color.lerp(textMuted, other.textMuted, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      accentHover: Color.lerp(accentHover, other.accentHover, t)!,
      accentPress: Color.lerp(accentPress, other.accentPress, t)!,
      onAccent: Color.lerp(onAccent, other.onAccent, t)!,
      readGreen: Color.lerp(readGreen, other.readGreen, t)!,
      favouriteGold: Color.lerp(favouriteGold, other.favouriteGold, t)!,
      cardBorder: Color.lerp(cardBorder, other.cardBorder, t)!,
      pagebgBlobOpacity: pagebgBlobOpacity + (other.pagebgBlobOpacity - pagebgBlobOpacity) * t,
    );
  }
}

class AppSpacing {
  AppSpacing._();

  static const radiusXs = 3.0;
  static const radiusSm = 6.0;
  static const radiusMd = 8.0;
  static const radiusLg = 10.0;
  static const radiusPill = 999.0;

  static const cardMin = 188.0; // was 150 — widened so 4 cards fit a row instead of 5
  static const cardGap = 14.0;
  static const coverRatio = 2 / 3;
}

class AppMotion {
  AppMotion._();

  static const railDuration = Duration(milliseconds: 180);
  static const railCurve = Cubic(0.4, 0, 0.2, 1);
  static const lift = 3.0;
}

// Text-style factory bound to a resolved AppColors palette — get an instance
// via AppText.of(context) rather than calling these as static members.
class AppText {
  final AppColors colors;
  const AppText(this.colors);

  static AppText of(BuildContext context) => AppText(AppColors.of(context));

  TextStyle _base({
    required double size,
    required FontWeight weight,
    double? letterSpacing,
    double? height,
    Color? color,
  }) {
    return GoogleFonts.hankenGrotesk(
      fontSize: size,
      fontWeight: weight,
      letterSpacing: letterSpacing,
      height: height,
      color: color ?? colors.textPrimary,
    );
  }

  TextStyle eyebrow({Color? color}) => _base(
        size: 11,
        weight: FontWeight.w700,
        letterSpacing: 11 * 0.08,
        color: color ?? colors.textMuted,
      );

  TextStyle titleLarge({Color? color}) => _base(
        size: 32,
        weight: FontWeight.w800,
        letterSpacing: 32 * -0.02,
        height: 1.1,
        color: color ?? colors.textPrimary,
      );

  TextStyle titleMedium({Color? color}) => _base(
        size: 30,
        weight: FontWeight.w800,
        letterSpacing: 30 * -0.02,
        height: 1.1,
        color: color ?? colors.textPrimary,
      );

  TextStyle countBig({Color? color}) => _base(
        size: 22,
        weight: FontWeight.w800,
        color: color ?? colors.accent,
      );

  TextStyle body({Color? color}) => _base(
        size: 15,
        weight: FontWeight.w400,
        height: 1.7,
        color: color ?? colors.textPrimary,
      );

  TextStyle label({
    double size = 14,
    FontWeight weight = FontWeight.w700,
    Color? color,
  }) =>
      _base(size: size, weight: weight, color: color ?? colors.textPrimary);

  TextStyle meta({
    double size = 12,
    Color? color,
  }) =>
      _base(size: size, weight: FontWeight.w400, color: color ?? colors.textMuted);

  TextStyle secondary({
    double size = 14,
    Color? color,
  }) =>
      _base(size: size, weight: FontWeight.w400, color: color ?? colors.textSecondary);
}

ThemeData _buildTheme(AppColors palette, Brightness brightness) {
  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: ColorScheme.fromSeed(
      seedColor: palette.accent,
      brightness: brightness,
      primary: palette.accent,
      surface: palette.surfaceCard,
    ),
    scaffoldBackgroundColor: palette.canvas,
    cardColor: palette.surfaceCard,
    dividerColor: palette.border,
    appBarTheme: AppBarTheme(
      backgroundColor: palette.surfaceCard,
      elevation: 0,
      centerTitle: false,
    ),
    tabBarTheme: const TabBarThemeData(
      dividerColor: Colors.transparent,
    ),
    extensions: [palette],
  );
  return base.copyWith(
    textTheme: GoogleFonts.hankenGroteskTextTheme(base.textTheme).apply(
      bodyColor: palette.textPrimary,
      displayColor: palette.textPrimary,
    ),
  );
}

ThemeData buildLightTheme() => _buildTheme(AppColors.light, Brightness.light);
ThemeData buildDarkTheme() => _buildTheme(AppColors.dark, Brightness.dark);
