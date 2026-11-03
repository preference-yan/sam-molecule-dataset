"""Verify the full archived inventory; never modify any data file."""
import collections
import csv
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "metadata/manifest.json").read_text())
    transfer = json.loads((root / "metadata/transfer_manifest.json").read_text())
    records = manifest["records"]
    require(len(records) == 5116, "Expected 5,116 structures")
    expected_counts = {"train": 4039, "val": 557, "test": 520}
    require(collections.Counter(r["split"] for r in records) == expected_counts,
            "Unexpected split counts")
    paths = {r["path"] for r in records}
    require(len(paths) == len(records), "Repeated manifest paths")
    actual_paths = {p.relative_to(root).as_posix() for p in (root / "data").rglob("*.extxyz")}
    require(actual_paths == paths, "Missing or unexpected structure files")
    for relative, expected in transfer["files"].items():
        path = root / relative
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                "Unsafe inventory path")
        require(path.is_file() and not path.is_symlink(), "Not a regular file: " + relative)
        require(path.stat().st_size == expected["bytes"], "Size mismatch: " + relative)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"],
                "SHA-256 mismatch: " + relative)
    identities = {split: set() for split in expected_counts}
    for record in records:
        path = record["path"]
        require(path == "data/" + record["split"] + "/" + record["file"], "Wrong path: " + path)
        require(transfer["files"][path]["sha256"] == record["sha256"], "Manifest hash mismatch")
        identities[record["split"]].add(record["canonical_smiles"])
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        require(not identities[a] & identities[b], "Molecular identity leakage: " + a + "/" + b)
    require({key: len(value) for key, value in identities.items()} ==
            {"train": 71, "val": 9, "test": 9}, "Unexpected molecule identity counts")
    with (root / "metadata/catalog.csv").open(newline="") as handle:
        catalog = list(csv.DictReader(handle))
    require(len(catalog) == 5116 and {r["path"] for r in catalog} == paths, "Catalog inventory mismatch")
    require(sum(float(r["adsorption_energy"]) > 0 for r in catalog) == 57,
            "Positive-energy records are missing")
    print(json.dumps({"verified_structures": len(records), "split_counts": expected_counts,
                      "molecule_identities": 89, "identity_overlap": 0,
                      "positive_energy_records": 57, "all_file_hashes_match": True}, indent=2))


if __name__ == "__main__":
    main()
