import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Base text style definitions using Google Fonts.
/// Georgian text: Noto Sans Georgian (height: 1.55)
/// Latin text: Inter
/// Legal citations: JetBrains Mono
class UiKitTextStyles {
  const UiKitTextStyles._();

  // ── Display Styles (for screen titles, hero text) ─────────────────

  static TextStyle get displayBold32 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w700,
        fontStyle: FontStyle.normal,
        fontSize: 32,
        height: 1.3,
      );

  static TextStyle get display32 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 32,
        height: 1.3,
      );

  // ── Headline Styles (section headers, card titles) ────────────────

  static TextStyle get headlineBold24 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 24,
        height: 1.35,
      );

  static TextStyle get headline24 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 24,
        height: 1.35,
      );

  static TextStyle get headlineBold20 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 20,
        height: 1.4,
      );

  static TextStyle get headline20 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 20,
        height: 1.4,
      );

  // ── Title Styles (subsection titles, list items) ──────────────────

  static TextStyle get titleBold18 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 18,
        height: 1.45,
      );

  static TextStyle get title18 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w500,
        fontStyle: FontStyle.normal,
        fontSize: 18,
        height: 1.45,
      );

  // ── Body Styles (primary reading text) ────────────────────────────

  static TextStyle get bodyBold16 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 16,
        height: 1.55,
      );

  static TextStyle get body16 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 16,
        height: 1.55,
      );

  static TextStyle get bodyBold14 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.55,
      );

  static TextStyle get body14 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.55,
      );

  // ── Label Styles (buttons, chips, tags, captions) ─────────────────

  static TextStyle get labelBold14 => GoogleFonts.inter(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.3,
      );

  static TextStyle get label14 => GoogleFonts.inter(
        fontWeight: FontWeight.w500,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.3,
      );

  static TextStyle get labelBold12 => GoogleFonts.inter(
        fontWeight: FontWeight.w600,
        fontStyle: FontStyle.normal,
        fontSize: 12,
        height: 1.3,
      );

  static TextStyle get label12 => GoogleFonts.inter(
        fontWeight: FontWeight.w500,
        fontStyle: FontStyle.normal,
        fontSize: 12,
        height: 1.3,
      );

  // ── Caption Styles (metadata, timestamps) ─────────────────────────

  static TextStyle get caption11 => GoogleFonts.inter(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 11,
        height: 1.3,
      );

  // ── Legal Citation Styles (monospace for article numbers) ─────────

  static TextStyle get legalCitation14 => GoogleFonts.jetBrainsMono(
        fontWeight: FontWeight.w500,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.4,
      );

  static TextStyle get legalCitation12 => GoogleFonts.jetBrainsMono(
        fontWeight: FontWeight.w500,
        fontStyle: FontStyle.normal,
        fontSize: 12,
        height: 1.4,
      );

  // ── Legal Body (for reading long legal articles) ──────────────────

  static TextStyle get legalBody16 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 16,
        height: 1.6,
      );

  static TextStyle get legalBody14 => GoogleFonts.notoSansGeorgian(
        fontWeight: FontWeight.w400,
        fontStyle: FontStyle.normal,
        fontSize: 14,
        height: 1.6,
      );
}
