import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import numpy as np, matplotlib.pyplot as plt
import prx_style as prx
prx.apply()
t = np.linspace(0, 10, 200)
gam = [0.1, 0.3, 0.5]
fig, axes = plt.subplots(1, 2, figsize=prx.figsize("double", aspect=0.36))
for g in gam:
    axes[0].plot(t, np.exp(-g*t)*np.cos(2*t)**2, label=rf"$\gamma={g}$")
axes[0].set_xlabel(r"$t$ ($\mu$s)"); axes[0].set_ylabel("Fidelity")
axes[0].legend()
x = np.random.default_rng(0).normal(size=(40, 40))
im = axes[1].imshow(x, cmap="RdBu_r"); fig.colorbar(im, ax=axes[1], label="Amplitude (arb. units)")
axes[1].plot([5, 30], [5, 30], "o", color="k")
axes[1].set_xlabel(r"$\theta$ (rad)"); axes[1].set_ylabel(r"$q$ (nm$^{-1}$)")
prx.panel_labels(axes, outside=True)
prx.save(fig, "after", formats=("png",))
