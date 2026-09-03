"""Extract aluminium demand, grid intensity and the smelter carbon budget from a GCAM run.

One GCAM scenario supplies a whole internally consistent world (demand + grid + budget); MPP is
the fixed asset layer run inside it, crossed with CCS regimes. This is the ambition-ladder design
(IDEA_A_running_context.md, 2026-09-02 decisions 10-12). Reads the local BaseX database written by
the user's GCAM runs.

Three products, all annual 2020-2050:
  demand_series(scen)     -> global primary-aluminium production, Mt (D5 global shortcut: the
                             global trajectory rides on MPP's own regional distribution).
  grid_intensity_mpp(scen)-> DataFrame [year x MPP region] gross grid CO2 intensity, t CO2/MWh,
                             GCAM 32 regions mapped onto MPP's 16 (mirrors pipeline/grid_intensity).
  smelter_budget(scen)    -> annual smelter allowance, Gt CO2/yr:
                             smelting_elec_emis (GCAM elec demand x GCAM own grid)
                           + anode_pfc(t) x production, anode_pfc declining on the scenario's own
                             industry-CO2 reduction fraction (decision 10). Refining is excluded
                             (separate refinery run), so no double count with GCAM's alumina CO2.

Anode/PFC factors are read from MPP itself: a grid-powered smelter tech's co2_scope1 is exactly
anode process + PFC + anode thermal (no captive power, no refining):
  Carbon Anode + Grid  = 2.093 t/t   Inert Anode + Grid = 0.063 t/t   (region-invariant).
"""

from pathlib import Path

import numpy as np
import pandas as pd
# gcamreader is imported lazily inside _db() so the cache loaders (load_demand/grid/budget) work
# under the model env, which need not have gcamreader or the GCAM DB installed.

GCAM_OUT = Path("/Users/parkercaswell/gcam/output")
DB = "database_basexdb"
QUERIES = GCAM_OUT / "queries" / "Main_queries.xml"

YEARS = list(range(2020, 2051))

# Trial ambition ladder = GCAM SSP-RCP pairs by forcing target (interim, mixed SSP1/SSP2 until
# GCAM SSP2-1.9/2.6 are run). NB these are SSP-RCP pairs, NOT the future CMIP7 VL/L scenarios that
# will replace them; keep the two label systems separate.
SCENARIOS = {
    "SSP1_1p9": "GCAM_SSP1_1p9",        # 1.9 W/m2 (~1.5 C)
    "SSP1_2p6": "GCAM_SSP1_2p6",        # 2.6 W/m2
    "SSP2_3p7": "GCAM_SSP2_3p7",        # 3.7 W/m2
    "SSP2_4p5": "GCAM_SSP2_4p5_tol15",  # 4.5 W/m2
}

# --- unit conversions ---
MTC_TO_MTCO2 = 44.0 / 12.0                       # GCAM CO2 is million tonnes CARBON
MT_PER_EJ_TO_T_PER_MWH = 1e6 / (1e18 / 3.6e9)    # = 0.0036, Mt CO2/EJ -> t CO2/MWh
EJ_TO_GT_CO2_AT = 2.777778e8 / 1e9               # EJ x (t/MWh) -> Gt CO2  (= 0.27778)

# --- MPP smelter anode+PFC factors, read from MPP (grid-powered tech scope1) ---
ANODE_CARBON = 2.093   # t CO2/t, Carbon Anode + Grid co2_scope1
ANODE_INERT = 0.063    # t CO2/t, Inert Anode + Grid co2_scope1

MPP_BASE_2020_MT = 65.4   # MPP calibrated 2020 primary production; demand bridges from here

# GCAM 2020 fleet init stays; 2020-2024 is spin-up, we anchor demand at 2025 and report 2025-2050.
ANCHOR_YEAR = 2025

# Each MPP region takes the grid of one GCAM region. China is one GCAM region -> all six MPP China
# regions share it (the crux, ~62% of output). Judgement calls flagged, mirroring
# pipeline/grid_intensity.py's R10 mapping.
MPP_TO_GCAM = {
    "China - Central": "China", "China - East": "China", "China - North": "China",
    "China - North East": "China", "China - North West": "China", "China - South": "China",
    "US": "USA",
    "Canada": "Canada",
    "Russia": "Russia",
    "Middle East": "Middle East",
    "Rest of Asia": "India",                          # dominant Asia-ex-China smelter region
    "Rest of Europe": "EU-15",
    "Scandinavia": "European Free Trade Association",  # Norway/Iceland hydro; judgement
    "Oceania": "Australia_NZ",                         # loses Japan/Korea (dirtier)
    "Africa": "South Africa",                          # smelter hub; N.Africa unresolved
    "South America": "Brazil",
}

INDUSTRY_SECTORS = [
    "alumina", "cement", "chemical energy use", "chemical feedstocks",
    "iron and steel", "other industrial energy use", "other industrial feedstocks",
    "process heat cement",
]

_conn = None
_queries = None
_cache = {}


def _db():
    global _conn, _queries
    if _conn is None:
        import gcamreader  # lazy: only needed to (re)build the cache, not to load it
        _conn = gcamreader.LocalDBConn(str(GCAM_OUT), DB, suppress_gabble=True)
        _queries = gcamreader.parse_batch_query(str(QUERIES))
    return _conn, _queries


def _q(title):
    _, qs = _db()
    hits = [x for x in qs if x.title == title]
    if not hits:
        raise KeyError(f"query not found: {title}")
    return hits[0]


def _run(title, scen):
    """Run one query for one scenario, memoised — the same big sector tables are reused across
    demand/grid/budget, so caching turns 3-4 BaseX hits per scenario into one."""
    ckey = (title, scen)
    if ckey not in _cache:
        conn, _ = _db()
        _cache[ckey] = conn.runQuery(_q(title), scenarios=[scen])
    return _cache[ckey]


def _to_annual(years, values):
    """Interpolate 5-yr GCAM points to annual over YEARS."""
    x = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    keep = ~np.isnan(y)
    return pd.Series(np.interp(YEARS, x[keep], y[keep]), index=YEARS)


# ---------------------------------------------------------------- demand
def demand_series(scen):
    """Global primary-aluminium production, Mt, annual. 2025 = GCAM; 2020-2024 bridges from the
    MPP base 65.4 up to GCAM's 2025, so MPP's 2020 fleet init is undisturbed (spin-up)."""
    key = SCENARIOS.get(scen, scen)
    d = _run("aluminum production by region", key)
    g = d.groupby("Year")["value"].sum()
    ann = _to_annual(g.index.to_list(), g.to_list())
    # bridge 2020 -> ANCHOR_YEAR linearly from the MPP base to GCAM's anchor value
    gcam_anchor = ann[ANCHOR_YEAR]
    for y in range(2020, ANCHOR_YEAR + 1):
        frac = (y - 2020) / (ANCHOR_YEAR - 2020)
        ann[y] = MPP_BASE_2020_MT + frac * (gcam_anchor - MPP_BASE_2020_MT)
    return ann


# ---------------------------------------------------------------- grid
def _region_series(df, region, value="value"):
    sub = df[df["region"] == region]
    if sub.empty:
        return None
    g = sub.groupby("Year")[value].sum()
    return _to_annual(g.index.to_list(), g.to_list())


def _gcam_grid_by_region(scen):
    """Gross grid intensity (t CO2/MWh) per GCAM region, annual. Gross = add BECCS-in-electricity
    back to the net elec CO2 (a smelter is not the beneficiary of economy-wide CDR)."""
    key = SCENARIOS.get(scen, scen)
    co2 = _run("CO2 emissions by sector (excluding resource production)", key)
    co2 = co2[co2["sector"].str.startswith("elec_", na=False)]
    seq = _run("CO2 sequestration by sector", key)
    seq = seq[seq["sector"].str.startswith("elec_biomass", na=False)] if seq is not None else None
    gen = _run("elec gen by region (incl CHP)", key)

    out = {}
    for region in gen["region"].unique():
        g = _region_series(gen, region)                       # EJ
        e = _region_series(co2, region)                       # MTC, net of BECCS
        if g is None or e is None:
            continue
        b = _region_series(seq, region) if seq is not None else None
        if b is None:
            b = pd.Series(0.0, index=YEARS)
        mtco2 = (e + b) * MTC_TO_MTCO2                         # Mt CO2 gross
        with np.errstate(divide="ignore", invalid="ignore"):
            out[region] = (mtco2 / g).replace([np.inf, -np.inf], np.nan).fillna(0.0) \
                * MT_PER_EJ_TO_T_PER_MWH
    return pd.DataFrame(out)


def grid_intensity_mpp(scen):
    """DataFrame [year x MPP region], gross grid CO2 intensity t CO2/MWh, GCAM->MPP mapped."""
    gcam = _gcam_grid_by_region(scen)
    mpp = {}
    for mpp_region, gcam_region in MPP_TO_GCAM.items():
        if gcam_region in gcam.columns:
            mpp[mpp_region] = gcam[gcam_region]
    return pd.DataFrame(mpp)


def world_grid_intensity(scen):
    """Global gross grid intensity, t CO2/MWh, annual (for the global smelter budget)."""
    key = SCENARIOS.get(scen, scen)
    co2 = _run("CO2 emissions by sector (excluding resource production)", key)
    co2 = co2[co2["sector"].str.startswith("elec_", na=False)]
    seq = _run("CO2 sequestration by sector", key)
    seq = seq[seq["sector"].str.startswith("elec_biomass", na=False)] if seq is not None else None
    gen = _run("elec gen by region (incl CHP)", key)

    e = _to_annual(*_group_year(co2))
    g = _to_annual(*_group_year(gen))
    b = _to_annual(*_group_year(seq)) if seq is not None and len(seq) else pd.Series(0.0, index=YEARS)
    return (e + b) * MTC_TO_MTCO2 / g * MT_PER_EJ_TO_T_PER_MWH


def _group_year(df):
    g = df.groupby("Year")["value"].sum()
    return g.index.to_list(), g.to_list()


# ---------------------------------------------------------------- budget
def industry_reduction_fraction(scen):
    """Scenario industry-CO2 reduction fraction, normalised to 1.0 at ANCHOR_YEAR. Drives the
    anode/PFC decline so anode ambition is scenario-consistent (fast at VL, slow at M)."""
    key = SCENARIOS.get(scen, scen)
    co2 = _run("CO2 emissions by sector (excluding resource production)", key)
    ind = co2[co2["sector"].isin(INDUSTRY_SECTORS)]
    total = _to_annual(*_group_year(ind))
    f = total / total[ANCHOR_YEAR]
    return f.clip(lower=0.0, upper=1.0)


def anode_pfc_intensity(scen):
    """Anode+PFC per tonne, t CO2/t, annual. Carbon-anode share declines on the scenario's own
    industry reduction fraction: intensity = inert_floor + (carbon - inert) * carbon_share."""
    carbon_share = industry_reduction_fraction(scen)          # 1.0 at anchor, falls after
    return ANODE_INERT + (ANODE_CARBON - ANODE_INERT) * carbon_share


def smelter_budget(scen):
    """Smelter allowance, Gt CO2/yr, annual: smelting electricity (GCAM demand x GCAM own grid)
    + anode/PFC x production. Refining excluded (separate refinery run)."""
    key = SCENARIOS.get(scen, scen)
    inp = _run("aluminum inputs by tech (energy and feedstocks)", key)
    elec = inp[inp["input"] == "elect_td_ind"]
    elec_ej = _to_annual(*_group_year(elec))                  # EJ, global smelting electricity
    grid = world_grid_intensity(scen)                         # t CO2/MWh
    elec_emis_gt = elec_ej * grid * EJ_TO_GT_CO2_AT           # Gt CO2

    prod = demand_series(scen)                                # Mt
    anode_gt = anode_pfc_intensity(scen) * prod / 1000.0      # Gt CO2

    total = (elec_emis_gt + anode_gt).rename("annual_limit")
    return pd.DataFrame({"smelting_elec": elec_emis_gt, "anode_pfc": anode_gt,
                         "annual_limit": total})


# ---------------------------------------------------------------- disk cache
# Extract once, then the runner and later sessions read these CSVs instead of querying BaseX
# (slow, and needs the GCAM DB present). Committed to the repo.
CACHE = Path(__file__).resolve().parent / "gcam_cache"


def build_cache():
    CACHE.mkdir(exist_ok=True)
    for tag in SCENARIOS:
        demand_series(tag).rename("value").rename_axis("year").to_frame() \
            .to_csv(CACHE / f"{tag}_demand.csv")
        grid_intensity_mpp(tag).rename_axis("year").to_csv(CACHE / f"{tag}_grid.csv")
        smelter_budget(tag).rename_axis("year").to_csv(CACHE / f"{tag}_budget.csv")
        print(f"cached {tag} -> {CACHE.name}/")


def load_demand(tag):
    return pd.read_csv(CACHE / f"{tag}_demand.csv", index_col="year")["value"]


def load_grid(tag):
    return pd.read_csv(CACHE / f"{tag}_grid.csv", index_col="year")


def load_budget(tag):
    return pd.read_csv(CACHE / f"{tag}_budget.csv", index_col="year")


# ---------------------------------------------------------------- self-test / summary
if __name__ == "__main__":
    build_cache()
    show = [2025, 2030, 2040, 2050]
    for tag in SCENARIOS:
        dem = demand_series(tag)
        bud = smelter_budget(tag)
        grid = grid_intensity_mpp(tag)
        china = grid["China - Central"] if "China - Central" in grid else None
        print(f"\n=== {tag} ({SCENARIOS[tag]}) ===")
        print("  demand Mt   :", "  ".join(f"{y}:{dem[y]:6.1f}" for y in show))
        if china is not None:
            print("  China t/MWh :", "  ".join(f"{y}:{china[y]:6.3f}" for y in show))
        print("  budget Gt/yr:", "  ".join(f"{y}:{bud['annual_limit'][y]:6.3f}" for y in show),
              "  (elec+anode)")
        print("    elec  Gt  :", "  ".join(f"{y}:{bud['smelting_elec'][y]:6.3f}" for y in show))
        print("    anode Gt  :", "  ".join(f"{y}:{bud['anode_pfc'][y]:6.3f}" for y in show))
        print("    anode t/t :", "  ".join(f"{y}:{anode_pfc_intensity(tag)[y]:6.3f}" for y in show))
