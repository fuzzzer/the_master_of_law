/// What a chip is sitting ON, so it can pick the correct recessed rung.
///
/// This is the **parent-aware surface rule** (`USING.md` §3) turned into an API
/// instead of a comment. A chip that sits directly on a page's `ground` chrome
/// draws its box in `surface`; the *same* chip inside a `surface` card or
/// bubble draws it in `ground`. Get it backwards and the chip either vanishes
/// into its parent or floats a rung too high.
///
/// **Shared deliberately** (M17 / `T-0261`). It began life as
/// `AppCitationParent`, private to one widget, while `_DomainChip` restated the
/// identical rule in a **comment** in two separate files — and the two copies
/// then diverged. One rule expressed three ways is how they drift; this enum is
/// the single place it is stated. Any further app-side chip takes this type.
enum AppChipParent {
  /// The chip sits on `ground` (page chrome, an AppBar, a list background)
  /// → its box is `surface`.
  ground,

  /// The chip sits inside a `surface` card or bubble → its box is `ground`.
  surface,
}
