"""
Reads computed values from the Excel model (single source of truth) and produces:
  1. Football field (valuation range by method)
  2. WACC / terminal growth sensitivity heatmap
  3. Year-1 net income bridge (accretion / dilution)

Run from the repo root:  python python/visualize.py
Note: the Excel file must have been saved by Excel/LibreOffice so formula values are cached.
"""
import os
import numpy as np
import openpyxl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "..", "excel_model", "SalesforceSlack_Valuation.xlsx")
OUT_DIR = os.path.join(HERE, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

wb = openpyxl.load_workbook(XLSX, data_only=True)

NAVY, BLUE, GRAY, RED, GREEN = "#1F4E78", "#4472C4", "#808080", "#C00000", "#548235"
plt.rcParams["axes.edgecolor"] = "#BFBFBF"

# ---------- 1. Football field ----------
ff = wb["Football Field"]
methods = [ff.cell(r, 1).value for r in range(5, 9)]
lows = [ff.cell(r, 2).value for r in range(5, 9)]
highs = [ff.cell(r, 3).value for r in range(5, 9)]

fig, ax = plt.subplots(figsize=(10, 4.5))
y = np.arange(len(methods))
ax.barh(y, [h - l for l, h in zip(lows, highs)], left=lows,
        color=[BLUE, BLUE, BLUE, RED], height=0.5, edgecolor="white")
ax.set_yticks(y)
ax.set_yticklabels(methods, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("Implied Value per Share ($)")
ax.set_title("Slack Valuation Football Field", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.set_xlim(-8, max(highs) + 14)
for i, (l, h) in enumerate(zip(lows, highs)):
    if i == 3:
        ax.text((l + h) / 2, i, f"\\${(l + h) / 2:.2f} (deal price)", va="center", ha="center",
                fontsize=9, fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.3", fc=RED, ec="none"))
    else:
        ax.text(l - 1.2, i, f"\\${l:.2f}", va="center", ha="right", fontsize=9, color=GRAY)
        ax.text(h + 1.2, i, f"\\${h:.2f}", va="center", ha="left", fontsize=9, color=GRAY)
plt.subplots_adjust(left=0.32, right=0.95, top=0.88, bottom=0.15)
plt.savefig(os.path.join(OUT_DIR, "01_football_field.png"), dpi=200, facecolor="white")
plt.close()

# ---------- 2. Sensitivity heatmap ----------
s = wb["Sensitivity"]
waccs = [s.cell(r, 1).value for r in range(5, 10)]
growths = [s.cell(4, c).value for c in range(2, 7)]
grid = np.array([[s.cell(r, c).value for c in range(2, 7)] for r in range(5, 10)])

fig, ax = plt.subplots(figsize=(8, 5.5))
im = ax.imshow(grid, cmap="RdYlGn", aspect="auto")
ax.set_xticks(range(5)); ax.set_xticklabels([f"{g:.1%}" for g in growths])
ax.set_yticks(range(5)); ax.set_yticklabels([f"{w:.1%}" for w in waccs])
ax.set_xlabel("Terminal Growth Rate"); ax.set_ylabel("WACC")
ax.set_title("DCF Value per Share: Sensitivity to WACC & Terminal Growth",
             fontsize=13, fontweight="bold", color=NAVY, pad=15)
for i in range(5):
    for j in range(5):
        base = (i == 2 and j == 2)
        ax.text(j, i, f"\\${grid[i, j]:.2f}", ha="center", va="center", fontsize=10,
                fontweight="bold" if base else "normal")
        if base:
            ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, edgecolor=NAVY, linewidth=3))
fig.colorbar(im, ax=ax, shrink=0.8).set_label("Value per Share ($)")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "02_sensitivity_heatmap.png"), dpi=200, facecolor="white")
plt.close()

# ---------- 3. Net income bridge ----------
ds = wb["Deal Structure"]
values = [ds["B19"].value, ds["B20"].value, -ds["B21"].value, ds["B22"].value, ds["B23"].value]
labels = ["Salesforce\nStandalone NI", "+ Slack\nStandalone NI", "- After-tax\nInterest",
          "+ Synergies\n(Yr 1)", "Pro Forma\nCombined NI"]
eps0, eps1, acc = ds["B30"].value, ds["B31"].value, ds["B32"].value

bottoms, heights, colors, cum = [], [], [], 0
for i, v in enumerate(values):
    if i in (0, len(values) - 1):
        bottoms.append(0); heights.append(v); colors.append(NAVY); cum = v
    else:
        bottoms.append(cum if v >= 0 else cum + v)
        heights.append(abs(v)); colors.append(GREEN if v >= 0 else RED); cum += v
min_vis = max(values[0], values[-1]) * 0.012
plot_h = [max(h, min_vis) if 0 < i < 4 else h for i, h in enumerate(heights)]

fig, ax = plt.subplots(figsize=(9.5, 5))
x = np.arange(5)
ax.bar(x, plot_h, bottom=bottoms, color=colors, width=0.6, edgecolor="white")
for i, (b, h, v) in enumerate(zip(bottoms, plot_h, values)):
    txt = f"\\${v:,.0f}M" if i in (0, 4) else f"{v:+,.0f}"
    ax.text(i, b + h + 40, txt, ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5)
ax.set_ylabel("Non-GAAP Net Income ($M)")
ax.set_title("Year-1 Pro Forma Net Income Bridge", fontsize=13, fontweight="bold", color=NAVY, pad=15)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.text(0.5, -0.22,
        f"Standalone EPS \\${eps0:.2f}  ->  Pro Forma EPS \\${eps1:.2f}   ({acc:+.1%} accretion/(dilution))",
        transform=ax.transAxes, ha="center", fontsize=11, fontweight="bold",
        color=RED if acc < 0 else GREEN)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "03_accretion_dilution_bridge.png"), dpi=200, facecolor="white")
plt.close()

print("Charts saved to", OUT_DIR)
