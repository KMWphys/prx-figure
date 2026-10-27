import numpy as np, matplotlib.pyplot as plt
t = np.linspace(0, 10, 200)
gam = [0.1, 0.3, 0.5]
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for g, c in zip(gam, ["tab:red", "tab:green", "tab:orange"]):
    axes[0].plot(t, np.exp(-g*t)*np.cos(2*t)**2, color=c, lw=0.3, label=f"gamma={g}")
axes[0].set_xlabel("time [us]"); axes[0].set_ylabel("Fidelity")
axes[0].legend(fontsize=6)
x = np.random.default_rng(0).normal(size=(40, 40))
im = axes[1].imshow(x, cmap="jet"); fig.colorbar(im, ax=axes[1])
axes[1].plot([5, 30], [5, 30], "o", ms=2, mfc="none")
axes[1].set_xlabel("theta"); axes[1].set_ylabel("q [1/nm]")
fig.savefig("before.png", dpi=150)
