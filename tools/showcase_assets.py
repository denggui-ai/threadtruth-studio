#!/usr/bin/env python3
"""Build display-only derivatives from the committed, published gallery records.

This deliberately does not use the historical local comparison-preview builder.
Original result PNGs and authorized demo JPEGs are never edited in place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path, PurePosixPath

from PIL import Image


GALLERY_PATH = "gallery/style24-comparison-20260929"
PRIMARY_PATH = "docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold"
BEIGE_PATH = "docs/demo/preview-sources/beige-blazer-denim-outfit"
PRIMARY_IMAGES = (
    "hero.jpg", "source-1-front.jpg", "source-2-hood-collar.jpg",
    "source-3-zipper-detail.jpg", "source-4-back.jpg",
    *(f"look-{number}.jpg" for number in range(1, 7)),
)
DISPLAY_PARAMETERS = {
    "operation": "resize-and-encode", "format": "WEBP", "max_width": 960,
    "quality": 82, "method": 6, "resample": "LANCZOS", "upscale": False,
    "crop": False, "retouch": False,
}
COPY_PARAMETERS = {"operation": "byte-identical-copy"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(value: str) -> str:
    """Require portable relative paths, including for manifest provenance."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("..", ".") for part in value.split("/")):
        raise ValueError(f"path escapes deployment scope: {value!r}")
    return path.as_posix()


def file_info(path: Path, *, image: bool = True) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing file or unsafe symlink: {path.name}")
    info = {"sha256": sha256(path), "bytes": path.stat().st_size}
    if image:
        try:
            with Image.open(path) as picture:
                picture.load()
                info["dimensions"] = list(picture.size)
                info["format"] = picture.format
        except (OSError, ValueError) as error:
            raise ValueError(f"invalid image: {path.name}") from error
    return info


def load_rights(path: Path, expected_cases: int | None = None) -> dict:
    rights = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rights, dict):
        raise ValueError("rights document must be an object")
    cases = rights.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("rights cases must be a nonempty array")
    if expected_cases is not None and len(cases) != expected_cases:
        raise ValueError(f"rights must contain {expected_cases} published cases")
    expected_counts = {
        "cases": len(cases), "local_images": len(cases) * 2, "held_pairs": 0,
        "published_pairs": len(cases), "published_images": len(cases) * 2,
    }
    if rights.get("counts") != expected_counts:
        raise ValueError("rights counts do not match published cases")
    styles = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("rights case must be an object")
        style = case.get("style", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", style) or style in styles:
            raise ValueError("rights contains invalid or duplicate style")
        styles.add(style)
        if case.get("status") != "published":
            raise ValueError(f"rights case is not published: {style}")
        for name in ("label", "reason", "source_page", "author_record", "license"):
            if not isinstance(case.get(name), str) or not case[name].strip():
                raise ValueError(f"rights missing {name}: {style}")
        for name in ("source_sha256", "identity_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", case.get(name, "")):
                raise ValueError(f"rights invalid {name}: {style}")
        images = case.get("images", [])
        if (not isinstance(images, list) or len(images) != 2
                or not all(isinstance(item, dict) for item in images)
                or {item.get("side") for item in images} != {"A", "B"}):
            raise ValueError(f"rights requires unique A/B sides: {style}")
        if {item.get("route") for item in images} != {"native", "web"}:
            raise ValueError(f"rights requires native/web routes per case: {style}")
        for image in images:
            if not re.fullmatch(r"[0-9a-f]{64}", image.get("sha256", "")):
                raise ValueError(f"rights invalid image sha256: {style}")
            dimensions = image.get("dimensions", [])
            if len(dimensions) != 2 or any(type(value) is not int or value <= 0 for value in dimensions):
                raise ValueError(f"rights invalid image dimensions: {style}")
    return rights


def authorized_copies(primary: dict, beige: dict) -> list[dict]:
    """Validate existing demo grants and derive only their fixed public asset set."""
    if not isinstance(primary, dict) or not isinstance(beige, dict):
        raise ValueError("demo rights documents must be objects")
    if (primary.get("schema_version") != "1.0" or primary.get("status") != "promoted"
            or primary.get("role") != "primary" or primary.get("primary_demo_status") != "ready"
            or primary.get("quality", {}).get("state") != "image-ready"
            or primary.get("human_review", {}).get("status") != "closed"
            or primary.get("ai_content_label", {}).get("status") != "required-and-disclosed"
            or primary.get("media_license", {}).get("id") != "CC0-1.0"):
        raise ValueError("primary rights are not approved for public display")
    for name in ("public_use_authorized", "project_media_policy_accepted", "source_model_display_authorized"):
        if primary.get("source_rights", {}).get(name) is not True:
            raise ValueError(f"primary rights authorization missing: {name}")
    assets = primary.get("assets", []) + [primary.get("hero", {})]
    if len(assets) != 11 or {item.get("path") for item in assets} != set(PRIMARY_IMAGES):
        raise ValueError("primary rights asset allowlist mismatch")
    copies = []
    for asset in assets:
        copies.append({
            "source_path": f"{PRIMARY_PATH}/{asset['path']}",
            "output_path": f"assets/primary/{asset['path']}",
            "sha256": asset.get("public_sha256", asset.get("sha256")),
            "bytes": asset.get("bytes"), "dimensions": [asset.get("width"), asset.get("height")],
            "format": "JPEG", "rights_path": "assets/primary/rights.json",
        })
    if (beige.get("schema_version") != "1.0" or beige.get("status") != "approved-for-preview"
            or beige.get("license", {}).get("id") != "ThreadTruth-Demo-Only-1.0"
            or beige.get("attestation", {}).get("physical_outfit") is not True
            or beige.get("attestation", {}).get("repository_and_release_demo_rights") is not True
            or beige.get("public_asset", {}).get("path") != "source.jpg"):
        raise ValueError("beige outfit rights are not approved for project display")
    asset = beige["public_asset"]
    copies.append({
        "source_path": f"{BEIGE_PATH}/source.jpg", "output_path": "assets/beige-outfit.jpg",
        "sha256": asset.get("sha256"), "bytes": asset.get("bytes"),
        "dimensions": [asset.get("width"), asset.get("height")],
        "format": "JPEG", "rights_path": "assets/beige-outfit-rights.json",
    })
    return copies


def expected_dimensions(dimensions: list[int]) -> list[int]:
    width, height = dimensions
    target_width = min(width, DISPLAY_PARAMETERS["max_width"])
    return [target_width, max(1, round(height * target_width / width))]


def assert_info(actual: dict, expected: dict, label: str) -> None:
    for field in ("sha256", "dimensions", "bytes", "format"):
        if field in expected and actual.get(field) != expected[field]:
            raise ValueError(f"{label}: {field} mismatch")


def build_assets(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    gallery = repo_root / GALLERY_PATH
    rights = load_rights(gallery / "rights.json")
    primary = json.loads((repo_root / PRIMARY_PATH / "rights.json").read_text())
    beige = json.loads((repo_root / BEIGE_PATH / "rights.json").read_text())
    copies = authorized_copies(primary, beige)
    originals = []
    # Validate every input before creating the first derivative.
    for case in rights["cases"]:
        for item in case["images"]:
            relative = f"images/{case['style']}/{item['side']}.png"
            info = file_info(gallery / relative)
            assert_info(info, {"sha256": item["sha256"], "dimensions": item["dimensions"], "format": "PNG"}, relative)
            originals.append((case, item, relative, info))
    for copy in copies:
        assert_info(file_info(repo_root / copy["source_path"]), copy, copy["source_path"])
    records = []
    for case, item, relative, source_info in originals:
        output = f"display/{case['style']}/{item['side']}.webp"
        target = gallery / output
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(gallery / relative) as original:
            picture = original.convert("RGBA" if "A" in original.getbands() else "RGB")
            size = expected_dimensions(list(picture.size))
            if list(picture.size) != size:
                picture = picture.resize(tuple(size), Image.Resampling.LANCZOS)
            picture.save(target, format="WEBP", quality=82, method=6)
        records.append({
            "kind": "comparison-display", "style": case["style"], "side": item["side"],
            "route": item["route"], "rights_path": "rights.json",
            "source": {"path": f"{GALLERY_PATH}/{relative}", **source_info},
            "output": {"path": output, **file_info(target)},
            "derivation": DISPLAY_PARAMETERS.copy(),
        })
    for copy in copies:
        source = repo_root / copy["source_path"]
        target = gallery / copy["output_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({
            "kind": "authorized-copy", "rights_path": copy["rights_path"],
            "source": {"path": copy["source_path"], **file_info(source)},
            "output": {"path": copy["output_path"], **file_info(target)},
            "derivation": COPY_PARAMETERS.copy(),
        })
    for source_path, output in (
        (f"{PRIMARY_PATH}/rights.json", "assets/primary/rights.json"),
        (f"{BEIGE_PATH}/rights.json", "assets/beige-outfit-rights.json"),
    ):
        source, target = repo_root / source_path, gallery / output
        shutil.copyfile(source, target)
        records.append({
            "kind": "rights-copy", "source": {"path": source_path, **file_info(source, image=False)},
            "output": {"path": output, **file_info(target, image=False)},
            "derivation": COPY_PARAMETERS.copy(),
        })
    manifest = {
        "schema_version": "1.0", "gallery_path": GALLERY_PATH,
        "rights_path": "rights.json", "rights_sha256": sha256(gallery / "rights.json"),
        "assets": records,
    }
    (gallery / "display-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    manifest = build_assets(args.root)
    results = [item for item in manifest["assets"] if item["kind"] == "comparison-display"]
    print(json.dumps({
        "display_images": len(results), "original_bytes": sum(x["source"]["bytes"] for x in results),
        "display_bytes": sum(x["output"]["bytes"] for x in results),
        "copied_assets": len(manifest["assets"]) - len(results),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
