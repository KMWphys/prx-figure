---
name: prx-figure
description: Re-plot or restyle existing scientific figures (matplotlib scripts, data files, or saved plots) to meet Physical Review X / APS Physical Review figure requirements - column width, minimum lettering and line sizes, (a)(b) panel labels, units in parentheses, accessible grayscale-safe colors, EPS/PDF/PNG export. Use when the user asks to make figures "PRX style", "APS style", "Physical Review format", or journal-ready for a Phys. Rev. submission. Do NOT use for posters, slides, or other journals' styles.
license: MIT
compatibility: Requires Python 3.9+ with matplotlib and numpy. LaTeX is optional (only for --usetex).
---

# PRX / APS figure restyling

Goal: turn an existing figure into one that passes APS Physical Review figure rules
**without changing the science** (same data, same curves, same axis ranges unless asked).

The full rule list with numbers is in `references/aps-figure-rules.md`. Read it before
the first figure in a session.

## Tools in this skill

- `scripts/prx_style.py` - importable helper. `apply()`, `figsize()`, `panel_labels()`,
  `audit()`, `save()`. Run it with `--help` for the API summary.
- `scripts/audit_figure.py` - runs an existing plotting script unchanged, intercepts its
  figures, and prints every rule violation. Use it before and after restyling.
- `assets/prx.mplstyle` - the matplotlib style sheet (usable without the helper:
  `plt.style.use("path/to/prx.mplstyle")`).

All paths are relative to this skill's directory. Resolve that directory first and pass
absolute paths when running the scripts from the user's project.

## Workflow

1. **Locate the source of each figure.** Look for the plotting script and data
   (`.py`, `.ipynb`, `.npz`, `.csv`, `.h5`, ...). Restyling must re-plot from data.
   - If only an image (`.png`, `.jpg`, `.pdf`) exists with no script or data, stop and ask
     the user for the data or script. Never trace or digitize values from an image
     without explicit permission, and never stretch a raster image to "fix" sizes.
2. **Audit the original.**
   `python <skill>/scripts/audit_figure.py path/to/plot_script.py --width single`
   Note the reported problems; they are the to-do list.
3. **Decide the width** with the user if it isn't obvious: `single` (8.5 cm, the default
   for one plot), `onehalf`, or `double` (dense multipanel figures). Keep aspect ratio
   close to the original unless asked.
4. **Make a restyled copy** of the script (`<name>_prx.py`); do not overwrite the
   original. Minimal edits:
   ```python
   import sys; sys.path.insert(0, "<skill>/scripts")
   import prx_style as prx
   prx.apply()                                   # style sheet + fonts
   fig, axes = plt.subplots(1, 2, figsize=prx.figsize("double", aspect=0.4))
   ... original plotting code, with hard-coded fontsize=/lw=/ms= removed ...
   prx.panel_labels(axes)                        # (a), (b), ...
   prx.audit(fig, width="double")                # must report 0 errors
   prx.save(fig, "figs/fig2")                    # -> fig2.pdf, fig2.eps, fig2.png
   ```
5. **Fix content rules** that styling cannot fix automatically:
   - Axis labels: quantity then units in parentheses, e.g. `r"$E$ (eV)"`, never `[eV]`.
   - Greek letters as symbols (`$\theta$`), never spelled out ("theta").
   - Curves distinguishable in grayscale: vary line style / marker as well as color.
   - No small open symbols, shading, or cross-hatching; data points at least 1 mm.
   - Legend or caption defines every symbol and curve.
   - Multiple panels in one figure file, labeled (a), (b), ...
6. **Re-audit** with `audit_figure.py` on the new script (or `prx.audit` inline) until it
   reports 0 errors; fix WARNs too, or tell the user why one stays. NOTEs are things to
   check by eye. Then **look at the PNG** yourself at 100% zoom to catch overlaps,
   clipped labels, or crowded legends that the audit cannot see.
7. **Report** to the user: files written, width used, what changed, and anything left for
   the caption (line-style key, any image brightness adjustments, color-online notes).

## Rules of thumb

- Never change data, fits, axis limits, or log/linear scaling unless the user asks.
- Remove per-call `fontsize=`, `linewidth=`, `markersize=` overrides so the style sheet
  governs; reintroduce one only if the audit still passes.
- Colormaps: use perceptually uniform maps (`viridis`, `cividis`) or a diverging map
  (`RdBu_r`) for signed data, with symmetric limits (`vmin=-v, vmax=v`) so zero is the
  midpoint; avoid `jet`/`rainbow`. Keep the original colormap only if the user insists.
- Colorbars and insets obey the same minimum lettering size.
- Use `--usetex` / `prx.apply(usetex=True)` only if LaTeX is installed and the user wants
  Computer Modern to match REVTeX body text; the default STIX fonts need no LaTeX.
- For color-online-only figures APS requires `.eps`/`.ps`; `prx.save` writes EPS by
  default. EPS has no transparency: `alpha` fills are rasterized or flattened, so check
  the EPS output when transparency is used.
