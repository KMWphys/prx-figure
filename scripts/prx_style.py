"""APS Physical Review / PRX figure helper for matplotlib.

Usage (inside a plotting script):

    import sys; sys.path.insert(0, "/path/to/prx-figure/scripts")
    import prx_style as prx
    prx.apply()                                        # style sheet + fonts
    fig, ax = plt.subplots(figsize=prx.figsize("single"))
    ...
    prx.panel_labels(axes)                             # only for multipanel figures
    prx.audit(fig, width="single")                     # prints problems, returns list
    prx.save(fig, "figs/fig1")                         # .pdf .eps .png

Run `python prx_style.py --help` for a summary.
"""
from __future__ import annotations

import os
import re
import string
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

HERE = Path(__file__).resolve().parent
STYLE_FILE = HERE.parent / "assets" / "prx.mplstyle"

MM_PER_IN = 25.4
PT_PER_IN = 72.0
PT_PER_MM = PT_PER_IN / MM_PER_IN  # 2.8346

# Widths in inches. Single column is stated by APS (8.5 cm, 3 3/8 in);
# 1.5 / 2 column follow the REVTeX two-column layout.
WIDTHS_IN = {"single": 3.375, "onehalf": 5.0, "double": 7.0}

# APS limits at final size
MIN_CAP_HEIGHT_MM = 2.0
MIN_MARKER_DIAM_MM = 1.0
MIN_LINEWIDTH_PT = 0.5
SMALL_OPEN_MARKER_MM = 1.5

GREEK = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
         "omicron pi rho sigma tau upsilon phi chi psi omega").split()
_GREEK_RE = re.compile(r"(?<![A-Za-z\\])(" + "|".join(GREEK) + r")(?![A-Za-z])", re.I)
_PANEL_RE = re.compile(r"^\s*\(?[a-z]\)\s*$")


# ----------------------------------------------------------------------------
# Style
# ----------------------------------------------------------------------------
def apply(usetex: bool = False) -> None:
    """Load the PRX style sheet. usetex=True switches to LaTeX Computer Modern."""
    plt.style.use(str(STYLE_FILE))
    if usetex:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}",
        })


def width_in(width) -> float:
    """'single' | 'onehalf' | 'double' | number in cm -> inches."""
    if isinstance(width, str):
        try:
            return WIDTHS_IN[width]
        except KeyError:
            raise ValueError(f"width must be one of {list(WIDTHS_IN)} or a number in cm")
    return float(width) / 2.54


def figsize(width="single", aspect: float = 0.75, height_cm: float | None = None):
    """Figure size (inches) at final printed width. aspect = height / width."""
    w = width_in(width)
    h = height_cm / 2.54 if height_cm is not None else w * aspect
    return (w, h)


def panel_labels(axes, labels=None, loc=(0.03, 0.97), outside=False, **kw):
    """Add (a), (b), ... to each Axes. outside=True puts them above-left of the frame."""
    axes = list(getattr(axes, "flat", axes)) if not isinstance(axes, mpl.axes.Axes) else [axes]
    labels = labels or [f"({c})" for c in string.ascii_lowercase]
    style = dict(fontsize=mpl.rcParams["axes.labelsize"], va="top", ha="left")
    style.update(kw)
    for ax, lab in zip(axes, labels):
        if outside:
            ax.annotate(lab, xy=(0, 1), xycoords="axes fraction", xytext=(-2, 2),
                        textcoords="offset points", va="bottom", ha="right",
                        fontsize=style["fontsize"])
        else:
            ax.text(*loc, lab, transform=ax.transAxes, **style)


def save(fig, stem, formats=("pdf", "eps", "png"), dpi=600):
    """Save at exact figure size (no bbox cropping, so the column width is kept)."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for ext in formats:
        p = stem.with_suffix("." + ext)
        fig.savefig(p, dpi=dpi)
        out.append(str(p))
    print("saved:", ", ".join(out))
    return out


# ----------------------------------------------------------------------------
# Audit
# ----------------------------------------------------------------------------
@dataclass
class Problem:
    level: str      # "ERROR" breaks an APS rule; "WARN" likely problem; "NOTE" check by eye
    where: str
    msg: str

    def __str__(self):
        return f"[{self.level}] {self.where}: {self.msg}"


_cap_cache: dict = {}


def _cap_ratio(fp: FontProperties) -> float:
    """Cap height / font size for this font, measured from the glyph 'H'."""
    key = (tuple(fp.get_family()), fp.get_name(), fp.get_weight(), fp.get_style())
    if key not in _cap_cache:
        try:
            p = TextPath((0, 0), "H", size=100, prop=fp)
            ext = p.get_extents()
            _cap_cache[key] = ext.height / 100.0
        except Exception:
            _cap_cache[key] = 0.68
    return _cap_cache[key]


def _axes_name(ax, fig):
    try:
        return f"axes {fig.axes.index(ax)}"
    except (ValueError, AttributeError):
        return "figure"


def _is_colorbar(ax):
    return getattr(ax, "_colorbar", None) is not None or ax.get_label() == "<colorbar>"


def _luminance(c):
    r, g, b, _ = to_rgba(c)
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def audit(fig=None, width="single", verbose=True):
    """Check a figure against APS rules at the target printed width.

    Returns a list of Problem. ERROR = violates an APS requirement.
    """
    fig = fig or plt.gcf()
    fig.canvas.draw()  # populate tick labels
    probs: list[Problem] = []
    target = width_in(width)
    fw, fh = fig.get_size_inches()
    scale = target / fw

    if abs(scale - 1) > 0.02:
        probs.append(Problem("WARN", "figure",
            f"drawn {fw*2.54:.1f} cm wide but target is {target*2.54:.1f} cm; every size "
            f"will be scaled by {scale:.2f} when placed. Redraw with prx.figsize('{width}')."
            if isinstance(width, str) else
            f"drawn {fw*2.54:.1f} cm wide, target {target*2.54:.1f} cm (scale {scale:.2f})."))

    # --- text (grouped by font size so tick labels give one line) -------------
    groups = {}
    script_notes = set()
    seen = set()
    for t in fig.findobj(mpl.text.Text):
        s = t.get_text()
        if not t.get_visible() or not s.strip() or id(t) in seen:
            continue
        seen.add(id(t))
        fp = t.get_fontproperties()
        size_pt = t.get_fontsize() * scale
        cap_mm = size_pt * _cap_ratio(fp) / PT_PER_MM
        short = s if len(s) < 30 else s[:27] + "..."
        if cap_mm < MIN_CAP_HEIGHT_MM - 1e-3:
            need = MIN_CAP_HEIGHT_MM * PT_PER_MM / _cap_ratio(fp) / scale
            key = (round(t.get_fontsize(), 2), round(need, 1))
            groups.setdefault(key, [cap_mm, []])[1].append(short)
        if ("_" in s or "^" in s) and "$" in s and cap_mm * 0.7 < MIN_CAP_HEIGHT_MM:
            script_notes.add(short)
    for (fs, need), (cap_mm, items) in sorted(groups.items()):
        ex = ", ".join(f"'{x}'" for x in items[:4]) + (f" +{len(items)-4} more" if len(items) > 4 else "")
        probs.append(Problem("ERROR", "text",
            f"{len(items)} text item(s) at {fs:g} pt -> cap height {cap_mm:.2f} mm < 2 mm "
            f"(need >= {need:.1f} pt at this figure size): {ex}"))
    if script_notes:
        probs.append(Problem("NOTE", "text",
            "sub/superscripts render at ~70% size, below 2 mm caps: "
            + ", ".join(f"'{x}'" for x in sorted(script_notes)[:4])
            + " - keep key numerals out of scripts or enlarge"))

    # axis labels: units and greek names
    for ax in fig.axes:
        for lab_obj in (ax.xaxis.label, ax.yaxis.label):
            lab = lab_obj.get_text()
            if not lab:
                continue
            where = _axes_name(ax, fig)
            if re.search(r"\[[^\]]+\]\s*$", lab):
                probs.append(Problem("ERROR", where,
                    f"label '{lab}' puts units in square brackets; APS uses parentheses"))
            plain = re.sub(r"\$[^$]*\$", "", lab)
            m = _GREEK_RE.search(plain)
            if m:
                probs.append(Problem("ERROR", where,
                    f"label '{lab}' spells out '{m.group(1)}'; use the symbol (e.g. $\\{m.group(1).lower()}$)"))
        if not _is_colorbar(ax) and ax.get_visible() and ax.axison:
            if not ax.get_xlabel() and ax.xaxis.get_visible() and any(
                    tl.get_text() for tl in ax.get_xticklabels()):
                probs.append(Problem("NOTE", _axes_name(ax, fig), "x axis has tick labels but no axis label"))
            if not ax.get_ylabel() and ax.yaxis.get_visible() and any(
                    tl.get_text() for tl in ax.get_yticklabels()):
                probs.append(Problem("NOTE", _axes_name(ax, fig), "y axis has tick labels but no axis label"))

    # --- lines and markers ---------------------------------------------------
    for ax in fig.axes:
        where = _axes_name(ax, fig)
        styles = []
        for ln in ax.get_lines():
            if not ln.get_visible():
                continue
            name = ln.get_label()
            name = "" if name.startswith("_") else f" '{name}'"
            disp = name.strip() or "unnamed line"
            ls = ln.get_linestyle()
            has_line = ls not in ("None", "none", "", " ") and len(ln.get_xdata()) > 1
            if has_line and ln.get_linewidth() * scale < MIN_LINEWIDTH_PT - 1e-6:
                probs.append(Problem("ERROR", where,
                    f"line{name} width {ln.get_linewidth()*scale:.2f} pt < 0.5 pt"))
            mk = ln.get_marker()
            if mk not in (None, "None", "none", "", " ", ","):
                d_mm = ln.get_markersize() * scale / PT_PER_MM
                if d_mm < MIN_MARKER_DIAM_MM:
                    probs.append(Problem("ERROR", where,
                        f"markers{name} {d_mm:.2f} mm < 1 mm diameter (markersize >= {MIN_MARKER_DIAM_MM*PT_PER_MM/scale:.1f})"))
                fc = ln.get_markerfacecolor()
                if (isinstance(fc, str) and fc.lower() == "none") or to_rgba(fc)[3] == 0:
                    if d_mm < SMALL_OPEN_MARKER_MM:
                        probs.append(Problem("WARN", where,
                            f"small open markers{name} ({d_mm:.2f} mm); APS asks to avoid small open symbols"))
            if mk == ",":
                probs.append(Problem("ERROR", where, f"pixel markers{name} are below 1 mm"))
            styles.append((disp, _luminance(ln.get_color()),
                           str(ls) if has_line else "none", str(mk)))

        for coll in ([] if _is_colorbar(ax) else ax.collections):
            if not coll.get_visible():
                continue
            cname = type(coll).__name__
            if cname == "PathCollection":  # scatter
                sizes = coll.get_sizes()
                if len(sizes):
                    d_mm = (min(sizes) ** 0.5) * scale / PT_PER_MM
                    if d_mm < MIN_MARKER_DIAM_MM:
                        probs.append(Problem("ERROR", where,
                            f"scatter points {d_mm:.2f} mm < 1 mm (s >= {(MIN_MARKER_DIAM_MM*PT_PER_MM/scale)**2:.0f})"))
            elif cname == "LineCollection":
                lws = coll.get_linewidths()
                if len(lws) and min(lws) * scale < MIN_LINEWIDTH_PT - 1e-6:
                    probs.append(Problem("ERROR", where,
                        f"line collection (e.g. error bars) width {min(lws)*scale:.2f} pt < 0.5 pt"))
            elif cname in ("PolyCollection", "FillBetweenPolyCollection"):
                probs.append(Problem("NOTE", where,
                    "shaded region (fill_between); APS discourages shading - make sure it survives grayscale"))
            if coll.get_hatch():
                probs.append(Problem("WARN", where, "cross-hatching used; APS asks to avoid it"))
            cmap = getattr(coll, "get_cmap", lambda: None)()
            if cmap is not None and cmap.name in ("jet", "rainbow", "hsv", "gist_rainbow", "nipy_spectral"):
                probs.append(Problem("WARN", where, f"colormap '{cmap.name}' is not accessible; use viridis/cividis/RdBu_r"))
        for im in ([] if _is_colorbar(ax) else ax.images):
            cm = im.get_cmap()
            if cm is not None and cm.name in ("jet", "rainbow", "hsv", "gist_rainbow", "nipy_spectral"):
                probs.append(Problem("WARN", where, f"colormap '{cm.name}' is not accessible; use viridis/cividis/RdBu_r"))
        for p in ax.patches:
            if p.get_hatch():
                probs.append(Problem("WARN", where, "cross-hatching used; APS asks to avoid it"))
                break

        # grayscale distinguishability
        for i in range(len(styles)):
            for j in range(i + 1, len(styles)):
                a, b = styles[i], styles[j]
                if abs(a[1] - b[1]) < 0.12 and a[2] == b[2] and a[3] == b[3]:
                    probs.append(Problem("WARN", where,
                        f"{a[0]} and {b[0]} look alike in grayscale (same line style and marker, "
                        "similar lightness); vary line style or marker"))

    # --- panel labels ------------------------------------------------------
    main_axes = [a for a in fig.axes if not _is_colorbar(a) and a.get_visible() and a.axison]
    if len(main_axes) > 1:
        texts = [t.get_text() for t in fig.findobj(mpl.text.Text)]
        if not any(_PANEL_RE.match(s) for s in texts):
            probs.append(Problem("ERROR", "figure",
                f"{len(main_axes)} panels but no (a), (b), ... labels; use prx.panel_labels()"))

    if verbose:
        n_err = sum(p.level == "ERROR" for p in probs)
        print(f"PRX audit ({width} column, {target*2.54:.1f} cm): "
              f"{len(probs)} problems ({n_err} errors)")
        for p in probs:
            print("  ", p)
    return probs


if __name__ == "__main__":
    print(__doc__)
    print("Widths (in):", WIDTHS_IN)
    print("Style file:", STYLE_FILE)
