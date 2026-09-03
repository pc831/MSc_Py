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

# Sixteen runs: four GCAM ambition scenarios (SSP-RCP pairs) crossed with four captive-power CCS
# regimes. Rows of every comparison figure are the CCS regime, columns are the ambition scenario.
#
# NAMING CONVENTION (keep consistent across code, runs/, gcam_cache/ and figures):
#   ambition scenario  code tag  SSP<n>_<forcing>   e.g. SSP1_1p9, SSP2_4p5   (== runs/ folder and
#                       pipeline/gcam_cache/ key); display "SSP1-1.9"; ordered by forcing ascending
#                       (1.9 -> 4.5 = most -> least ambitious). These are SSP-RCP pairs, NOT the
#                       future CMIP7 VL/L scenarios — keep the two label systems separate.
#   CCS regime          none | low | high | unlimited
#   cell id             "<ambition>_<ccs>"  e.g. SSP1_1p9_none   (== the runs/ folder name)
#
#   capture   none       captive-power carbon capture barred entirely
#             low        annual capture addition capped at the nuclear-analogue diffusion rate
#             high       capped at the global flue-gas-desulfurisation rate
#             unlimited  no cap (the unconstrained reference; also the capture-fleet reference)
ARCHIVE = SCENARIOS_DIR.parent / "_archive" / "scenarios_92switches"

AMBITION = ["SSP1_1p9", "SSP1_2p6", "SSP2_3p7", "SSP2_4p5"]      # ordered most -> least ambitious
AMBITION_LABELS = {"SSP1_1p9": "SSP1-1.9", "SSP1_2p6": "SSP1-2.6",
                   "SSP2_3p7": "SSP2-3.7", "SSP2_4p5": "SSP2-4.5"}
CCS_ORDER = ["none", "low", "high", "unlimited"]
CCS_LABELS = {"none": "No CCS", "low": "Low Limit CCS",
              "high": "High Limit CCS", "unlimited": "Unlimited CCS"}

# Read out under every comparison figure, so a reader who has not followed the work can
# understand the axes without asking.
CAPTION = (
    "Columns are the GCAM ambition scenario (SSP-RCP pair) supplying the smelter's demand, grid "
    "intensity and carbon budget: SSP1-1.9, SSP1-2.6, SSP2-3.7 and SSP2-4.5, spanning most- to "
    "least-ambitious mitigation. (Interim stand-in GCAM runs.)\n"
    "Rows are the constraint on captive-power carbon capture. No CCS bars captive-power capture "
    "entirely. Low caps the annual capture addition at the nuclear-analogue diffusion rate "
    "(1.45% of the captive fossil fleet per year, Kazlou et al. 2024). High caps it at the "
    "global flue-gas-desulfurisation rate (10.7% per year, van Ewijk & McDowall 2020). "
    "Unlimited applies no cap. Each column holds its own GCAM demand, grid and budget fixed, so "
    "within a column only the capture constraint varies."
)

RUNS_INDEX = {}
for _amb in AMBITION:
    for _ccs in CCS_ORDER:
        _name = f"{_amb}_{_ccs}"
        RUNS_INDEX[_name] = {"ambition": _amb, "ccs": _ccs, "base": RUNS}


def run_name(ambition, ccs):
    return f"{ambition}_{ccs}"


# Full matrix, ambition-major so a column (one scenario) is contiguous.
SCENARIOS = [run_name(a, c) for a in AMBITION for c in CCS_ORDER]

LABELS = {_n: f"{AMBITION_LABELS[_r['ambition']]}, {_r['ccs']} CCS" for _n, _r in RUNS_INDEX.items()}

# One hue per ambition scenario, so a colour means the same scenario in every figure.
AMBITION_COLOURS = {"SSP1_1p9": "#9b2226", "SSP1_2p6": "#b45309",
                    "SSP2_3p7": "#003f88", "SSP2_4p5": "#386641"}
COLOURS = {_n: AMBITION_COLOURS[_r["ambition"]] for _n, _r in RUNS_INDEX.items()}

# Backward-compatible aliases: the second axis was the IAM grid, it is now the ambition scenario.
# Existing plot code that iterates GRIDS or keys on GRID_LABELS/GRID_COLOURS keeps working.
GRIDS = AMBITION
GRID_LABELS = AMBITION_LABELS
GRID_COLOURS = AMBITION_COLOURS

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

# Refining is inert to both levers (no grid exposure, no capture route), so it is identical
# across the matrix. It is run once and every refinery request resolves to that single run.
REFINERY_REF = "REFINERY_REF"


def interface(scenario, plant):
    """The model's own output table for one run, technology rows only."""
    if plant == "refinery":
        scenario = REFINERY_REF
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


def budget(plant, scenario=None):
    """The annual carbon budget the run was actually solved against, Mt CO2.

    Read from inputs_used (the GCAM budget written by run_gcam_ladder, not model_clean's shipped
    budget). In the ambition ladder the smelter budget differs by ambition scenario, so pass a
    cell id of that scenario (any CCS cell serves — the CCS regime does not change the budget).
    Refining is unpatched, so its budget is MPP's shipped one, from the canonical refinery run.
    """
    if plant == "refinery":
        ref = REFINERY_REF
    else:
        ref = scenario or SCENARIOS[0]
    path = RUNS / ref / plant / "inputs_used" / "carbon_budget.csv"
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


def capture_grid(figsize=(13.5, 11.0), sharey=True):
    """The 4 by 4 comparison layout: CCS regime down the rows, ambition scenario across columns.

    Returns (fig, axes) where axes is keyed by (ccs, ambition). Every comparison figure uses this
    same layout so a reader learns it once.
    """
    fig, axes = plt.subplots(len(CCS_ORDER), len(AMBITION),
                             figsize=figsize, sharex=True, sharey=sharey)
    lookup = {}
    for row, ccs in enumerate(CCS_ORDER):
        for col, grid in enumerate(AMBITION):
            ax = axes[row, col]
            lookup[(ccs, grid)] = ax
            ax.set_xlim(2020, 2050)
            ax.set_xticks([2020, 2030, 2040, 2050])
            ax.tick_params(labelsize=10)
            if row == 0:
                ax.set_title(GRID_LABELS[grid], fontsize=11, fontweight="bold")
    return fig, lookup


def label_rows(axes, unit):
    """Row labels (CCS regime) outboard in bold, one non-bold unit label inboard of them.

    Order independent: it forces a draw first, so it works whether it is called before or
    after tight_layout.
    """
    fig = axes[(CCS_ORDER[0], GRIDS[0])].figure
    fig.canvas.draw()
    for ccs in CCS_ORDER:
        box = axes[(ccs, GRIDS[0])].get_position()
        fig.text(0.008, (box.y0 + box.y1) / 2, CCS_LABELS[ccs], rotation=90,
                 ha="left", va="center", fontsize=12, fontweight="bold")
    top = axes[(CCS_ORDER[0], GRIDS[0])].get_position()
    bottom = axes[(CCS_ORDER[-1], GRIDS[0])].get_position()
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
