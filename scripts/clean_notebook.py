"""Strip widget metadata from notebooks so they render on GitHub.

Usage:
    python scripts/clean_notebook.py notebooks/01_eda.ipynb
    python scripts/clean_notebook.py notebooks/*.ipynb
"""

import json
import sys
from pathlib import Path


def clean_notebook(path: Path) -> bool:
    """Remove problematic widget metadata. Returns True if changes made."""
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    changed = False

    # Strip widget metadata from notebook level
    if "widgets" in nb.get("metadata", {}):
        del nb["metadata"]["widgets"]
        changed = True

    # Strip widget metadata from individual cells
    for cell in nb.get("cells", []):
        if "metadata" in cell:
            for key in ["widgets", "execution"]:
                if key in cell["metadata"]:
                    del cell["metadata"][key]
                    changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")

    return changed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/clean_notebook.py <notebook>...")
        sys.exit(1)

    for arg in sys.argv[1:]:
        for path in Path(".").glob(arg) if "*" in arg else [Path(arg)]:
            if path.suffix != ".ipynb":
                continue
            if clean_notebook(path):
                print(f"Cleaned widget metadata from {path}")
            else:
                print(f"No changes needed for {path}")


if __name__ == "__main__":
    main()
