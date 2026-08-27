"""Asset transition milestone figure for the aluminium pathway.

One horizontal row per technology group per region. The bar spans the transition window,
from the year no new unabated capacity may be added to the year the technology is gone, so
the length of the bar is the managed decline period rather than an arbitrary distance from
zero. Phase-out years set by the 2050 net zero backstop rather than read off the source
scenario are drawn hollow, because they mark where the pathway departs from its source.

Years come from derive_milestones.py via milestones_aluminium.csv.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

DATA_DIR = Path(".")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.titlepad": 10,
    "axes.labelsize": 11,
    "axes.grid": True,
    "grid.linewidth": 0.5,
    "grid.color": "#cccccc",
    "grid.alpha": 0.7,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.frameon": False,
    "legend.fontsize": 10,
    "figure.dpi": 100,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
})

# Dark and light shade of one hue, so the region comparison reads within every group.
REGION_COLOR = {"China": "#003f88", "RoW": "#0096c7"}
REGION_LABEL = {"China": "China", "RoW": "Rest of the World"}

# Group order top to bottom, with the label used on the axis.
GROUPS = [("Unabated fossil digester", "Unabated fossil digester"),
          ("Unabated fossil calciner", "Unabated fossil calciner"),
          ("Unabated carbon anode", "Unabated carbon anode"),
          ("Unabated fossil auxiliary", "Unabated fossil auxiliary")]

# The specification asks for a phase-out milestone only on the anode, so no no-new marker is
# drawn for it. The derived years are noted on the figure instead.
NO_NEW_SPECIFIED = {"Unabated fossil digester", "Unabated fossil calciner",
                    "Unabated fossil auxiliary"}

milestones = pd.read_csv(DATA_DIR / "milestones_aluminium.csv")
milestones = milestones.set_index(["Group", "Region"])

fig, ax = plt.subplots(figsize=(11, 6))

labels, positions = [], []
y = 0
for group, group_label in GROUPS:
    for region in ["China", "RoW"]:
        row = milestones.loc[(group, region)]
        color = REGION_COLOR[region]
        no_new = int(row["No New Year"])
        phase_out = int(row["Phase Out Year"])
        backstop = bool(row["Phase Out From Backstop"])

        if group in NO_NEW_SPECIFIED:
            # Transition window: no new capacity may be added, existing capacity runs down.
            ax.plot([no_new, phase_out], [y, y], color=color, linewidth=7, alpha=0.30,
                    solid_capstyle="butt", zorder=1)
            ax.plot(no_new, y, marker="|", color=color, markersize=17,
                    markeredgewidth=3, zorder=3)
            ax.annotate(f"{no_new}", (no_new, y), xytext=(-7, 0),
                        textcoords="offset points", ha="right", va="center",
                        fontsize=9.5, color=color)

        # Hollow phase-out marker where the year comes from the backstop, not the scenario.
        ax.plot(phase_out, y, marker="o", color=color, markersize=9,
                markerfacecolor="white" if backstop else color,
                markeredgewidth=2.2, zorder=3)
        ax.annotate(f"{phase_out}", (phase_out, y), xytext=(9, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=9.5, color=color,
                    fontstyle="italic" if backstop else "normal")

        labels.append(f"{group_label}, {REGION_LABEL[region]}")
        positions.append(y)
        y -= 1
    y -= 0.6          # breathing room between technology groups

ax.axvline(2050, color="#999999", linewidth=1, linestyle=(0, (4, 3)), zorder=0)

ax.set_yticks(positions)
ax.set_yticklabels(labels)
ax.set_ylim(y + 0.4, 0.9)
ax.set_xlim(2018, 2054)
ax.set_xticks(range(2020, 2051, 5))
ax.set_xlabel("Year")
ax.grid(axis="x")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", length=0)

ax.set_title("Asset transition milestones for unabated technologies in the SBTi aluminium "
             "sector pathway", pad=34)
ax.annotate("MPP 1.5DS for digester, calciner and anode, IAI 1.5DS for auxiliary. "
            "Captive power generation is out of scope, so it carries no milestone here.",
            xy=(0, 1.012), xycoords="axes fraction", fontsize=9.5, color="#555555")

handles = [
    # Grey, because the window itself appears in both region colours.
    Line2D([], [], color="#999999", linewidth=7, alpha=0.45,
           label="Transition window, no new capacity but existing capacity still running"),
    Line2D([], [], color="#333333", marker="|", linestyle="none", markersize=17,
           markeredgewidth=3, label="No new unabated capacity"),
    Line2D([], [], color="#333333", marker="o", linestyle="none", markersize=9,
           markeredgewidth=2.2, label="Phase out, read off the source scenario"),
    Line2D([], [], color="#333333", marker="o", linestyle="none", markersize=9,
           markerfacecolor="white", markeredgewidth=2.2,
           label="Phase out, set by the 2050 net zero requirement"),
    Line2D([], [], color=REGION_COLOR["China"], linewidth=4, label="China"),
    Line2D([], [], color=REGION_COLOR["RoW"], linewidth=4, label="Rest of the World"),
]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2,
          frameon=False)

ax.annotate("The specification sets a phase-out milestone only for the carbon anode. The "
            "derived no new capacity years are 2021 for China and 2033 for the Rest of the "
            "World.",
            xy=(0, -0.42), xycoords="axes fraction", fontsize=9, color="#555555")

plt.tight_layout()
plt.savefig(DATA_DIR / "fig_milestones.png")
print("wrote fig_milestones.png")
