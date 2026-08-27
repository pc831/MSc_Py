"""Figures for the scenario deck annex."""

import glob
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

FIG = Path("figures")
SCENARIOS = [
    "BAU",
    "LC_MPPgrid_limitedCCS_AnodeLocked",
    "LC_SBTigrid_limitedCCS_AnodeLocked",
    "LC_MPPgrid_limitedCCS_AnodeUnlocked",
    "LC_SBTigrid_limitedCCS_AnodeUnlocked",
]
LABELS = {
    "BAU": "Business as usual",
    "LC_MPPgrid_limitedCCS_AnodeLocked": "MPP grid,\ninert anode locked",
    "LC_SBTigrid_limitedCCS_AnodeLocked": "SBTi grid,\ninert anode locked",
    "LC_MPPgrid_limitedCCS_AnodeUnlocked": "MPP grid,\ninert anode unlocked",
    "LC_SBTigrid_limitedCCS_AnodeUnlocked": "SBTi grid,\ninert anode unlocked",
}
COLOURS = {
    "BAU": "#4a4a4a",
    "LC_MPPgrid_limitedCCS_AnodeLocked": "#c0504d",
    "LC_SBTigrid_limitedCCS_AnodeLocked": "#e8a33d",
    "LC_MPPgrid_limitedCCS_AnodeUnlocked": "#4f81bd",
    "LC_SBTigrid_limitedCCS_AnodeUnlocked": "#1f4e79",
}
PLANTS = {"smelter": "Aluminium smelting", "refinery": "Alumina refining"}

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def load(scenario, plant):
    path = glob.glob(f"runs/{scenario}/{plant}/final/interface_outputs_*.csv")[0]
    df = pd.read_csv(path)
    return df[df["technology"] != "All"]


def emissions(scenario, plant):
    """Scope 1 plus scope 2 by year, in Mt CO2."""
    df = load(scenario, plant)
    scope1 = df[df["parameter"] == "CO2 Scope1"].groupby("year")["value"].sum()
    scope2 = df[df["parameter"] == "CO2 Scope2"].groupby("year")["value"].sum()
    return scope1 + scope2


def budget(plant):
    folder = "def" if plant == "smelter" else "def_refineries"
    df = pd.read_csv(f"models/model_clean/aluminium/data/lc/{folder}/intermediate/carbon_budget.csv")
    series = df.set_index("year")["annual_limit"] * 1000
    return series.loc[2020:2050]


# Figure 1 — emissions against the carbon budget
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (plant, title) in zip(axes, PLANTS.items()):
    for scenario in SCENARIOS:
        series = emissions(scenario, plant)
        ax.plot(series.index, series.values, label=LABELS[scenario].replace("\n", " "), color=COLOURS[scenario], lw=2)
    limit = budget(plant)
    ax.plot(limit.index, limit.values, "k--", lw=1.5, label="1.5°C budget")
    ax.set_title(title)
    ax.set_ylabel("Mt CO$_2$ per year")
    ax.set_xlim(2020, 2050)
    ax.set_ylim(bottom=0)
axes[0].legend(fontsize=8, frameon=False)
fig.suptitle("Annual emissions against the sector carbon budget", y=1.0, fontsize=12)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(FIG / f"fig1_emissions_vs_budget.{ext}", dpi=200, bbox_inches="tight")

# Figure 2 — cumulative emissions against the budget
fig, ax = plt.subplots(figsize=(9.5, 4.4))
total_budget = budget("smelter").sum() + budget("refinery").sum()
names, values = [], []
for scenario in SCENARIOS:
    total = sum(emissions(scenario, plant).sum() for plant in PLANTS)
    names.append(LABELS[scenario].replace("\n", "\n"))
    values.append(total / 1000)
bars = ax.bar(names, values, color=[COLOURS[s] for s in SCENARIOS], width=0.55)
ax.axhline(total_budget / 1000, color="k", ls="--", lw=1.5)
ax.text(len(SCENARIOS) - 0.55, total_budget / 1000 + 0.5, f"Budget {total_budget/1000:.1f} Gt",
        ha="right", fontsize=9)
for bar, value in zip(bars, values):
    over = 100 * (value / (total_budget / 1000) - 1)
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.5,
            f"{value:.1f} Gt\n{over:+.0f}%", ha="center", fontsize=9)
ax.set_ylabel("Cumulative CO$_2$ 2020–2050, Gt")
ax.set_title("Cumulative emissions, both plant types combined")
ax.set_ylim(0, max(values) * 1.2)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(FIG / f"fig2_cumulative.{ext}", dpi=200, bbox_inches="tight")

# Figure 3 — smelter power source mix over time, one panel per scenario
POWER_GROUPS = {
    "Captive fossil": ["+ Coal", "+ Natural Gas"],
    "Captive fossil with capture": ["+ Coal+CCS", "+ Natural Gas+CCS"],
    "Grid and PPA": ["+ Grid", "+ PPA+Grid"],
    "Hydro": ["+ Hydro"],
    "Nuclear": ["+ Small Modular Reactor"],
}
# Fixed colour per group so the same colour means the same thing in every panel
GROUP_COLOURS = {
    "Captive fossil": "#6e6e6e",
    "Captive fossil with capture": "#c0504d",
    "Grid and PPA": "#f2c14e",
    "Hydro": "#9dc3e6",
    "Nuclear": "#31859c",
}


def power_group(technology):
    """Classify a smelter technology by its power source, longest suffix first."""
    for group, suffixes in POWER_GROUPS.items():
        for suffix in sorted(suffixes, key=len, reverse=True):
            if technology.endswith(suffix):
                return group
    return "Other"


fig, axes = plt.subplots(1, 5, figsize=(13.0, 3.9), sharey=True)
for ax, scenario in zip(axes, SCENARIOS):
    df = load(scenario, "smelter")
    volume = df[df["parameter"] == "Annual production volume"].copy()
    volume["group"] = volume["technology"].apply(power_group)
    table = volume.pivot_table(index="year", columns="group", values="value", aggfunc="sum")
    # Every group appears in every panel, at zero if absent, so colours never shift
    ordered = list(POWER_GROUPS)
    table = table.reindex(columns=ordered).fillna(0)
    ax.stackplot(table.index, table[ordered].T.values, labels=ordered,
                 colors=[GROUP_COLOURS[g] for g in ordered])
    ax.set_title(LABELS[scenario], fontsize=9)
    ax.set_xlim(2020, 2050)
axes[0].set_ylabel("Mt aluminium per year")
axes[-1].legend(fontsize=7, loc="upper right", frameon=False)
fig.suptitle("Smelter electricity supply", y=1.0, fontsize=12)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(FIG / f"fig3_smelter_power.{ext}", dpi=200, bbox_inches="tight")

# Figure 4 — refinery boiler mix over time
def boiler_group(technology):
    boiler = technology.split(" + ")[0]
    if boiler in ["Gas-Boiler", "Oil-Boiler", "Coal-Boiler"]:
        return "Unabated fossil boiler"
    if boiler in ["Elec-Boiler", "H2-Boiler", "Bio-Boiler"]:
        return "Electric, hydrogen or biomass"
    return "Heat recovery and solar thermal"


fig, axes = plt.subplots(1, 5, figsize=(13.0, 3.9), sharey=True)
order = ["Unabated fossil boiler", "Heat recovery and solar thermal", "Electric, hydrogen or biomass"]
for ax, scenario in zip(axes, SCENARIOS):
    df = load(scenario, "refinery")
    volume = df[df["parameter"] == "Annual production volume"].copy()
    volume["group"] = volume["technology"].apply(boiler_group)
    table = volume.pivot_table(index="year", columns="group", values="value", aggfunc="sum")
    table = table.reindex(columns=order).fillna(0)
    ax.stackplot(table.index, table[order].T.values, labels=order,
                 colors=["#6e6e6e", "#f2c14e", "#9dc3e6"])
    ax.set_title(LABELS[scenario], fontsize=9)
    ax.set_xlim(2020, 2050)
axes[0].set_ylabel("Mt alumina per year")
axes[-1].legend(fontsize=7, loc="upper right", frameon=False)
fig.suptitle("Refinery digester technology", y=1.0, fontsize=12)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(FIG / f"fig4_refinery_boiler.{ext}", dpi=200, bbox_inches="tight")

# Figure 5 — emissions intensity
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (plant, title) in zip(axes, PLANTS.items()):
    for scenario in SCENARIOS:
        df = load(scenario, plant)
        production = df[df["parameter"] == "Annual production volume"].groupby("year")["value"].sum()
        intensity = emissions(scenario, plant) / production
        ax.plot(intensity.index, intensity.values, label=LABELS[scenario].replace("\n", " "), color=COLOURS[scenario], lw=2)
    ax.set_title(title)
    ax.set_ylabel("t CO$_2$ per tonne of product")
    ax.set_xlim(2020, 2050)
    ax.set_ylim(bottom=0)
axes[0].legend(fontsize=8, frameon=False)
fig.suptitle("Emissions intensity", y=1.0, fontsize=12)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(FIG / f"fig5_intensity.{ext}", dpi=200, bbox_inches="tight")

print("written:", sorted(p.stem for p in FIG.glob("fig*.png")))
