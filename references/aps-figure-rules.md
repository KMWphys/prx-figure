# APS Physical Review figure rules (applies to PRX)

Summarized from the APS author "Style Basics" page
(https://journals.aps.org/authors/style-basics) and the APS Journals Style Guide.
Re-check that page if a requirement seems to have changed.

## Hard requirements and how the skill enforces them

| Rule (APS) | Value | Enforced by |
|---|---|---|
| Single-column width | 8.5 cm = 3 3/8 in | `prx.figsize("single")` |
| Wider figures | 1.5 or 2 columns, only for detailed figures | `"onehalf"` (~12.7 cm / 5.0 in), `"double"` (~17.8 cm / 7.0 in)* |
| Smallest capital letters and numerals | height >= 2 mm at final size | `audit()` measures the real cap height of the font in use |
| Data point diameter | >= 1 mm (~2.83 pt) | `audit()` (`markersize`, scatter `s`) |
| Curve line width | >= 0.18 mm = 0.5 pt | `audit()`; style uses 1.0 pt for data |
| Small open symbols, shading, cross-hatching | avoid | `audit()` flags open markers < 1.5 mm, hatches, filled bands |
| Axis labels | quantity, then units in parentheses: `Energy (eV)`, not `[eV]` | `audit()` flags `[...]` |
| Greek letters | use the symbol (θ), not the name ("theta") | `audit()` flags spelled-out names outside math |
| Multipanel figures | label (a), (b), ...; one file if possible; caption describes each panel | `prx.panel_labels()`; `audit()` checks presence |
| Symbols and curves | defined in a legend or in the caption | manual / report to user |
| Color | accessible palettes; for color-online-only figures, colors must have clearly different grayscale values and curves should also differ by line style | style cycle = Okabe-Ito colors x line styles; `audit()` grayscale check |
| Image adjustments | any brightness/contrast change must be stated in caption | report to user |
| File formats | .ps, .eps, .jpg, .png preferred; color-online-only requires .ps/.eps; photos as high-res .jpg/.png; scans >= 600 dpi | `prx.save()` writes .eps + .pdf + 600 dpi .png |

*APS states the single-column width explicitly. The 1.5- and 2-column values are the
REVTeX two-column layout (text width ~ 7.0 in); confirm against the current PRX template
if exact width matters.

## Derived numbers used by the style sheet

- 2 mm cap height ~ 8.3-8.7 pt font size depending on typeface (cap height is ~0.66-0.70
  of the font size). The style uses 9 pt tick labels and legends, 10 pt axis labels, so
  it passes with margin. Sub/superscripts in math are scaled by ~0.7; keep important
  numerals out of subscripts or enlarge them.
- 1 mm marker diameter = 2.83 pt; the style default is `lines.markersize: 4`.
- These limits apply at the **final printed size**. A figure drawn at 6.4 in wide and
  shrunk to 3.375 in loses ~47% of every size. Always draw at the final width.

## Content conventions (not automatically checkable)

- Label every axis with the plotted quantity. Use units in parentheses; for
  dimensionless or normalized quantities, say so (e.g. `$t/T$`, `Fidelity`).
- Avoid powers of ten in labels when an SI prefix works (`$t$ (μs)`).
- Use consistent symbols with the text (same notation as equations).
- Legends should not hide data; prefer placing them in empty regions or in the caption.
- Insets and colorbars follow the same size rules.
