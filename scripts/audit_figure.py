#!/usr/bin/env python3
"""Run an existing matplotlib plotting script unchanged and audit its figures
against APS / PRX rules.

    python audit_figure.py plot_script.py [--width single|onehalf|double|<cm>]
                           [--allow-save] [-- script args...]

By default the script's own savefig() calls are intercepted (nothing is written),
so auditing never overwrites the user's figures. Exit code 1 if any ERROR is found.
"""
import argparse
import os
import runpy
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prx_style  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--width", default="single")
    ap.add_argument("--allow-save", action="store_true", help="let the script write its files")
    argv = sys.argv[1:]
    script_args = []
    if "--" in argv:
        i = argv.index("--")
        argv, script_args = argv[:i], argv[i + 1:]
    a = ap.parse_args(argv)
    width = a.width
    try:
        width = float(width)
    except ValueError:
        pass

    captured = []
    orig_savefig = Figure.savefig

    def savefig(self, fname, *args, **kw):
        if self not in captured:
            captured.append(self)
        if a.allow_save:
            return orig_savefig(self, fname, *args, **kw)
        print(f"(audit) intercepted savefig -> {fname}")

    Figure.savefig = savefig
    plt.show = lambda *args, **kw: None

    script = Path(a.script).resolve()
    sys.argv = [str(script)] + script_args
    cwd = os.getcwd()
    os.chdir(script.parent)
    sys.path.insert(0, str(script.parent))
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        os.chdir(cwd)

    for num in plt.get_fignums():
        f = plt.figure(num)
        if f not in captured:
            captured.append(f)

    if not captured:
        print("No figures found.")
        return 1
    n_err = 0
    for i, fig in enumerate(captured, 1):
        print(f"\n=== Figure {i} ===")
        probs = prx_style.audit(fig, width=width)
        n_err += sum(p.level == "ERROR" for p in probs)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
