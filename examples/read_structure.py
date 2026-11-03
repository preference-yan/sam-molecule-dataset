"""Read one original composite without changing its file or labels."""
import json
from pathlib import Path

from ase.io import read

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "metadata/manifest.json").read_text())
record = next(row for row in manifest["records"] if row["split"] == "train")
with (root / record["path"]).open() as handle:
    atoms = read(handle, format="extxyz", index=0)

tags = atoms.get_tags()
substrate = atoms[tags == 0]
sam = atoms[tags == 2]
print({"file": record["path"], "total_atoms": len(atoms),
       "sam_atoms": len(sam), "substrate_atoms": len(substrate),
       "adsorption_energy": atoms.info["adsorption_energy"]})
