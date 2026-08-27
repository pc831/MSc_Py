"""Run one MPP aluminium scenario and save its outputs under scenarios/runs/<name>/<plant>/.

Usage:
    python run.py <scenario_name> <pathway> <plant>

    scenario_name  folder to save results in, e.g. BAU
    pathway        bau | lc | fa | cc
    plant          smelter | refinery

The model copy lives in scenarios/models/<model_dir> and writes into its own data folders.
This script sets the two config lines that choose the run, executes it, then
copies the results out so nothing is overwritten by the next run.
"""

import shutil
import subprocess
import sys
from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent
# Which model copy to run. Scenarios that change the model's inputs or code get their
# own copy so earlier scenarios stay reproducible.
MODEL_NAME = sys.argv[4] if len(sys.argv) > 4 else "model_clean"
MODEL_DIR = SCENARIOS_DIR / "models" / MODEL_NAME
CONFIG = MODEL_DIR / "aluminium" / "config_aluminium.py"

# Each plant type is a separate model run with its own data folder and product.
PLANT_SETTINGS = {
    "smelter": {"folder": "def", "product": "Aluminium"},
    "refinery": {"folder": "def_refineries", "product": "Alumina"},
}


def set_config(pathway, plant):
    """Rewrite the two config lines that select which run happens."""
    settings = PLANT_SETTINGS[plant]
    text = CONFIG.read_text()
    lines = text.splitlines(keepends=True)

    # Replace the whole SENSITIVITIES block with a single active pathway
    start = next(i for i, l in enumerate(lines) if l.startswith("SENSITIVITIES = {"))
    end = next(i for i, l in enumerate(lines[start:], start) if l.startswith("}"))
    lines[start : end + 1] = [
        "SENSITIVITIES = {\n",
        f'    "{pathway}": ["{settings["folder"]}"],\n',
        "}\n",
    ]

    # Replace the PRODUCTS line
    for i, l in enumerate(lines):
        if l.startswith("PRODUCTS = "):
            lines[i] = f'PRODUCTS = ["{settings["product"]}"]\n'

    CONFIG.write_text("".join(lines))


def run_model():
    """Execute the model and stream its output to the console."""
    return subprocess.run(
        [sys.executable, "main.py"], cwd=MODEL_DIR, capture_output=True, text=True
    )


def save_outputs(scenario_name, pathway, plant):
    """Copy the model's results into scenarios/<name>/<plant>/."""
    settings = PLANT_SETTINGS[plant]
    source = MODEL_DIR / "aluminium" / "data" / pathway / settings["folder"]
    destination = SCENARIOS_DIR / "runs" / scenario_name / plant
    destination.mkdir(parents=True, exist_ok=True)

    for subfolder in ["final", "stack_tracker", "ranking"]:
        if (source / subfolder).exists():
            target = destination / subfolder
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source / subfolder, target)

    # Keep a copy of the inputs that produced this run, so results stay traceable
    inputs_target = destination / "inputs_used"
    if inputs_target.exists():
        shutil.rmtree(inputs_target)
    shutil.copytree(source / "intermediate", inputs_target)

    return destination


scenario_name, pathway, plant = sys.argv[1], sys.argv[2], sys.argv[3]
assert plant in PLANT_SETTINGS, f"plant must be smelter or refinery, got {plant}"

print(f"Running {scenario_name}: pathway={pathway}, plant={plant}")
set_config(pathway, plant)
result = run_model()

if result.returncode != 0:
    print(result.stdout[-3000:])
    print(result.stderr[-3000:])
    sys.exit(f"Model run failed for {plant}")

destination = save_outputs(scenario_name, pathway, plant)
print(f"Saved to {destination}")
