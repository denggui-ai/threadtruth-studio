#!/usr/bin/env python3
"""Build and verify website-sized copies of the existing owned pose references."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "skills/lookset/references/pose-library"
GALLERY = "gallery/style24-comparison-20260929"
MANIFEST = "assets/poses/manifest.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(root=ROOT):
    return json.loads((root / SOURCE / "catalog.json").read_text())["entries"]


def output_path(entry):
    return "assets/poses/" + Path(entry["path"]).with_suffix(".webp").name


def allowed_files(root=ROOT):
    return {MANIFEST, "pose-showcase.css", "pose-showcase.js", *(output_path(e) for e in records(root))}


def build(root=ROOT):
    gallery = root / GALLERY
    assets = []
    for entry in records(root):
        source = root / SOURCE / entry["path"]
        assert digest(source) == entry["sha256"], entry["path"]
        output = gallery / output_path(entry)
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((840, 1120), Image.Resampling.LANCZOS)
            image.save(output, "WEBP", quality=84, method=6)
            size = list(image.size)
        assets.append({"path": output_path(entry), "group_id": entry["group_id"], "view": entry["view"],
                       "source": f"{SOURCE}/{entry['path']}", "source_sha256": entry["sha256"],
                       "sha256": digest(output), "bytes": output.stat().st_size, "dimensions": size,
                       "selection_policy": entry.get("selection_policy", "default")})
    manifest = {"source_id": "threadtruth-owned-poses-v1", "ai_generated": True,
                "derivation": "resize-and-webp-only; no crop or content edits", "actions": 52, "views": 60,
                "scope": "Adult womenswear AI or faceless planning references; not garment or identity evidence.",
                "assets": assets}
    (gallery / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {len(assets)} existing pose derivatives: {sum(a['bytes'] for a in assets):,} bytes")


def validate(gallery, root=ROOT):
    findings = []
    try:
        manifest = json.loads((gallery / MANIFEST).read_text())
        source = records(root)
        expected = {output_path(e): e for e in source}
        assets = manifest["assets"]
        assert manifest["actions"] == len({e["group_id"] for e in source}) == 52
        assert manifest["views"] == len(source) == len(assets) == 60
        assert {a["path"] for a in assets} == set(expected)
        assert manifest["ai_generated"] is True
        for asset in assets:
            entry = expected[asset["path"]]
            path = gallery / asset["path"]
            assert not path.is_symlink()
            assert asset["source"] == f"{SOURCE}/{entry['path']}"
            assert asset["source_sha256"] == entry["sha256"] == digest(root / asset["source"])
            assert asset["group_id"] == entry["group_id"] and asset["view"] == entry["view"]
            assert asset["selection_policy"] == entry.get("selection_policy", "default")
            assert digest(path) == asset["sha256"] and path.stat().st_size == asset["bytes"]
            with Image.open(path) as image:
                assert image.format == "WEBP" and list(image.size) == asset["dimensions"]
                assert image.width <= 840 and image.height <= 1120
        assert sum(a["bytes"] for a in assets) < 3_000_000
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        findings.append(f"pose showcase assets mismatch: {error}")
    return findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    if args.command == "build":
        build()
    else:
        failures = validate(ROOT / GALLERY)
        print("\n".join(failures) if failures else "PASS: 52 actions / 60 existing pose assets")
        raise SystemExit(bool(failures))
