import json
from pathlib import Path

notebook_path = Path("notebooks/01_eda.ipynb")

with open(notebook_path) as f:
    nb = json.load(f)

if "widgets" in nb.get("metadata", {}):
    del nb["metadata"]["widgets"]
    print("Removed metadata.widgets")
else:
    print("No metadata.widgets found")

cells_cleaned = 0
for cell in nb.get("cells", []):
    if "outputs" in cell:
        original_count = len(cell["outputs"])
        cell["outputs"] = [
            out
            for out in cell["outputs"]
            if "application/vnd.jupyter.widget-view+json" not in out.get("data", {})
            and "application/vnd.google.colaboratory.intrinsic+json" not in out.get("data", {})
        ]
        if len(cell["outputs"]) != original_count:
            cells_cleaned += 1

print(f"Cleaned widget outputs from {cells_cleaned} cells")

with open(notebook_path, "w") as f:
    json.dump(nb, f, indent=1)

print(f"Saved cleaned notebook to {notebook_path}")
