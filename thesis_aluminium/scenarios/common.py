"""Shared loading, scenario registry and plot helpers for the aluminium scenario notebooks.

Notebooks live in notebooks/analysis/ and notebooks/plots/ and reach this with:

    import sys; sys.path.append("../..")
    from common import ...

All runs are on MPP's full 132-pair switch table. Sections 23 and 24 of MODEL_REFERENCE.md
explain why, and the superseded 92-pair runs are in ../_archive/scenarios_92switches/.

Layout: models/ holds the model copies, runs/ holds their outputs, notebooks/ holds the
analysis and plotting notebooks, figures/ holds the rendered figures.
"""

from pathlib import Path

import glob
import matplotlib.pyplot as plt
import pandas as pd

SCENARIOS_DIR = Path(__file__).resolve().parent   # resolve, so notebooks importing
                                                 # this from a subfolder still get absolute paths
RUNS = SCENARIOS_DIR / "runs"        # one folder per scenario, the model's saved outputs
MODELS = SCENARIOS_DIR / "models"    # one working copy of MPP's model per scenario
FIG = SCENARIOS_DIR / "figures"

# Tonnes of alumina per tonne of aluminium, MPP's fixed conversion factor
ALUMINA_PER_ALUMINIUM = 1.935

# Twelve 1.5C runs plus business as usual. Three things vary.
#
#   capture   noCCS       MPP's shipped 92-pair switch table. Capture-equipped power is
#                         unreachable, so every run returns exactly zero. Superseded, archived,
#                         kept only as evidence. See MODEL_REFERENCE.md section 24.
#             limitedCCS  MPP's full table, with captive power capture held to the world rate
#                         in IEA WEO 2024 NZE. The defensible set.
#             CCS         MPP's full table with no limit at all. The unconstrained reference.
#   grid      MPP or SBTi power pathway emissions intensity
#   anode     Locked or Unlocked, our six added power-source switches
ARCHIVE = SCENARIOS_DIR.parent / "_archive" / "scenarios_92switches"

CAPTURE_ORDER = ["noCCS", "limitedCCS", "CCS"]
CAPTURE_LABELS = {"noCCS": "No CCS", "limitedCCS": "Limited CCS", "CCS": "Unlimited CCS"}
COLUMN_ORDER = [("MPP", "Locked"), ("SBTi", "Locked"), ("MPP", "Unlocked"), ("SBTi", "Unlocked")]
COLUMN_LABELS = {("MPP", "Locked"): "MPP grid\ninert anode locked",
                 ("SBTi", "Locked"): "SBTi grid\ninert anode locked",
                 ("MPP", "Unlocked"): "MPP grid\ninert anode unlocked",
                 ("SBTi", "Unlocked"): "SBTi grid\ninert anode unlocked"}

# Read out under every comparison figure, so a reader who has not followed the work can
# understand the axes without asking.
CAPTION = (
    "Rows are carbon capture regimes. No CCS is MPP's switch table exactly as shipped, in "
    "which every route into capture-equipped captive power is missing, so capture is "
    "unreachable and the run returns zero. Limited CCS uses MPP's full switch table with "
    "capture held to the rate the world fossil power fleet reaches in IEA WEO 2024 Net Zero, "
    "41% of coal and 12% of gas capacity by 2050, enforced through MPP's own CO2 storage "
    "constraint. Unlimited CCS uses the full table with no cap.\n"
    "Columns pair a grid emissions assumption with a switch table rule. Inert anode locked is "
    "MPP's table as they wrote it, which lets a smelter change its power source only while it "
    "still has a carbon anode; once the anode is converted the power source is frozen and the "
    "plant is stranded on captive coal or gas. Inert anode unlocked adds the six missing "
    "switches so a converted plant can still move to grid supply, a power purchase agreement "
    "or a small modular reactor."
)

RUNS_INDEX = {}
for _capture in CAPTURE_ORDER:
    for _grid, _anode in COLUMN_ORDER:
        _name = f"LC_{_grid}grid_{_capture}_Anode{_anode}"
        RUNS_INDEX[_name] = {"capture": _capture, "grid": _grid, "anode": _anode,
                             "base": ARCHIVE if _capture == "noCCS" else RUNS}
RUNS_INDEX["BAU"] = {"capture": "CCS", "grid": "MPP", "anode": "Locked", "base": RUNS}


def run_name(capture, grid, anode):
    return f"LC_{grid}grid_{capture}_Anode{anode}"


# The headline set: business as usual plus the four limited-capture runs.
SCENARIOS = ["BAU"] + [run_name("limitedCCS", g, a) for g, a in COLUMN_ORDER]

LABELS = {"BAU": "Business as usual"}
for _name, _r in RUNS_INDEX.items():
    if _name != "BAU":
        LABELS[_name] = (f"{_r['grid']} grid, inert anode {_r['anode'].lower()}")

# One hue per column, so a colour means the same grid and anode choice in every figure
COLUMN_COLOURS = {("MPP", "Locked"): "#9b2226", ("SBTi", "Locked"): "#b45309",
                  ("MPP", "Unlocked"): "#003f88", ("SBTi", "Unlocked"): "#386641"}
COLOURS = {"BAU": "#4a4a4a"}
for _name, _r in RUNS_INDEX.items():
    if _name != "BAU":
        COLOURS[_name] = COLUMN_COLOURS[(_r["grid"], _r["anode"])]

PLANTS = {"smelter": "Aluminium smelting", "refinery": "Alumina refining"}
DATA_FOLDER = {"smelter": "def", "refinery": "def_refineries"}


def style():
    """House matplotlib settings. Call once at the top of a notebook."""
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
    })


# ---------------------------------------------------------------- loading

def interface(scenario, plant):
    """The model's own output table for one run, technology rows only."""
    base = RUNS_INDEX.get(scenario, {}).get("base", RUNS)
    pattern = str(base / scenario / plant / "final" / "interface_outputs_*.csv")
    df = pd.read_csv(glob.glob(pattern)[0])
    return df[df["technology"] != "All"]


def _by_year(scenario, plant, parameter):
    df = interface(scenario, plant)
    return df[df["parameter"] == parameter].groupby("year")["value"].sum().loc[2020:2050]


def emissions(scenario, plant):
    """Scope 1 plus scope 2 by year, Mt CO2."""
    return _by_year(scenario, plant, "CO2 Scope1") + _by_year(scenario, plant, "CO2 Scope2")


def production(scenario, plant):
    """Annual production volume by year, Mt of product."""
    return _by_year(scenario, plant, "Annual production volume")


def production_by_technology(scenario, plant):
    """Annual production volume, years as rows and technologies as columns, Mt."""
    df = interface(scenario, plant)
    df = df[df["parameter"] == "Annual production volume"]
    pivot = df.pivot_table(index="year", columns="technology", values="value", aggfunc="sum")
    return pivot.reindex(range(2020, 2051)).fillna(0.0)


def budget(plant):
    """MPP's annual carbon budget for one plant type, Mt CO2."""
    path = (MODELS / "model_clean" / "aluminium" / "data" / "lc"
            / DATA_FOLDER[plant] / "intermediate" / "carbon_budget.csv")
    series = pd.read_csv(path).set_index("year")["annual_limit"] * 1000
    return series.loc[2020:2050]


# ------------------------------------------------- process versus electricity

def anode(technology):
    """The anode half of a '<anode> + <power source>' smelter technology name."""
    return technology.split(" + ", 1)[0]


def power_source(technology):
    """The power source half of a smelter technology name."""
    return technology.split(" + ", 1)[1]


def process_emission_factors():
    """Smelter process emission factor per anode type, tCO2 per tonne aluminium.

    Read directly off the model's own emission factors: the scope 1 of any technology whose
    power source is not captive fossil contains no power generation, so it is the pure anode
    figure (anode CO2, PFCs and anode thermal). Verified constant across all 16 regions and
    all years: Carbon Anode 2.093, Carbon Anode+CCS 1.135, Inert Anode 0.063.
    """
    path = (MODELS / "model_clean" / "aluminium" / "data" / "lc" / "def"
            / "intermediate" / "emissions.csv")
    em = pd.read_csv(path)
    em["anode"] = em["technology"].map(anode)
    em["power"] = em["technology"].map(power_source)
    no_captive = em[~em["power"].str.contains("Coal|Natural Gas")]
    return no_captive.groupby("anode")["co2_scope1"].first()


def intensity_split(scenario):
    """Emissions intensity split into process and electricity, tCO2e per tonne aluminium.

    Process is smelter anode emissions plus all alumina refining emissions, which are
    entirely process: refinery scope 2 is nonzero in only 26 of 12,524 rows and never exceeds
    0.024. Electricity is everything else on the smelter side, which is captive fossil
    generation reported inside scope 1 plus purchased power reported as scope 2.

    Refining is divided by aluminium production rather than alumina production, so it is
    already on a per tonne of aluminium basis. That works globally because the model holds
    alumina output at 1.92 to 1.95 times aluminium output, close to its fixed 1.935 factor.
    No regional attribution rule is involved.
    """
    factors = process_emission_factors()

    smelt = production_by_technology(scenario, "smelter")
    aluminium = smelt.sum(axis=1)

    # Process emissions are production times the anode factor, technology by technology
    smelter_process = sum(smelt[t] * factors[anode(t)] for t in smelt.columns)
    smelter_total = emissions(scenario, "smelter")
    refinery_total = emissions(scenario, "refinery")

    return pd.DataFrame({
        "Process": (smelter_process + refinery_total) / aluminium,
        "Electricity": (smelter_total - smelter_process) / aluminium,
    }).assign(Total=lambda d: d["Process"] + d["Electricity"])


# ---------------------------------------------------------------- plotting

def overlaid(figsize=(11, 6)):
    """One axes carrying every scenario as a line. Returns (fig, ax)."""
    return plt.subplots(figsize=figsize)


def panels(ncols=5, figsize=(18, 4.0), sharey=True):
    """One panel per scenario, in the order of SCENARIOS. Returns (fig, dict of axes)."""
    nrows = -(-len(SCENARIOS) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, sharey=sharey, sharex=True)
    flat = axes.flatten()
    for extra in flat[len(SCENARIOS):]:
        extra.set_visible(False)
    return fig, dict(zip(SCENARIOS, flat))


def year_axis(ax):
    ax.set_xlim(2020, 2050)
    ax.set_xticks(range(2020, 2051, 10))


def capture_grid(figsize=(13.5, 9.0), sharey=True):
    """The 3 by 4 comparison layout: capture regime down the rows, grid and anode across.

    Returns (fig, axes) where axes is keyed by (capture, grid, anode). Every comparison figure
    uses this same layout so a reader learns it once.
    """
    fig, axes = plt.subplots(len(CAPTURE_ORDER), len(COLUMN_ORDER),
                             figsize=figsize, sharex=True, sharey=sharey)
    lookup = {}
    for row, capture in enumerate(CAPTURE_ORDER):
        for col, (grid, anode) in enumerate(COLUMN_ORDER):
            ax = axes[row, col]
            lookup[(capture, grid, anode)] = ax
            ax.set_xlim(2020, 2050)
            ax.set_xticks([2020, 2030, 2040, 2050])
            ax.tick_params(labelsize=10)
            if row == 0:
                ax.set_title(COLUMN_LABELS[(grid, anode)], fontsize=11, fontweight="bold")
    return fig, lookup


def label_rows(axes, unit):
    """Row labels outboard in bold, one non-bold unit label inboard of them.

    Order independent: it forces a draw first, so it works whether it is called before or
    after tight_layout.
    """
    fig = axes[(CAPTURE_ORDER[0], *COLUMN_ORDER[0])].figure
    fig.canvas.draw()
    for capture in CAPTURE_ORDER:
        box = axes[(capture, *COLUMN_ORDER[0])].get_position()
        fig.text(0.008, (box.y0 + box.y1) / 2, CAPTURE_LABELS[capture], rotation=90,
                 ha="left", va="center", fontsize=12, fontweight="bold")
    top = axes[(CAPTURE_ORDER[0], *COLUMN_ORDER[0])].get_position()
    bottom = axes[(CAPTURE_ORDER[-1], *COLUMN_ORDER[0])].get_position()
    fig.text(0.048, (top.y1 + bottom.y0) / 2, unit, rotation=90,
             ha="left", va="center", fontsize=10.5, color="#333333")


def add_caption(fig, y=0.015, width=150):
    """A prose caption under the figure, left aligned and wrapped by hand."""
    import textwrap
    wrapped = []
    for paragraph in CAPTION.split("\n"):
        wrapped += textwrap.wrap(paragraph, width=width)
        wrapped.append("")
    fig.text(0.015, y, "\n".join(wrapped).rstrip(), ha="left", va="bottom",
             fontsize=9, color="#333333", linespacing=1.6)


def save(fig, name):
    """Write a figure to figures/ as both png and svg."""
    FIG.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"{name}.{ext}")
    print(f"wrote figures/{name}.png and .svg")
