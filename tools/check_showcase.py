#!/usr/bin/env python3
"""Check committed showcase assets before Pages upload; never regenerates files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from . import showcase_assets as assets
    from . import brand_assets as brand
except ImportError:
    import showcase_assets as assets
    import brand_assets as brand


REVIEWED_CASE_IDS = ("red-floral-french", "green-shirt-home", "trim-tee-american", "trim-tee-japanese", "external-black-leather", "black-jacket-office")
EXTERNAL_INPUT = "assets/reviewed-cases/external-black-leather/input.jpg"
OFFICE_INPUT = "assets/reviewed-cases/black-jacket-office/input.jpg"
HOME_PRESENTATION_FILES = (
    "assets/reviewed-cases/green-shirt-home/shirt-reference.jpg",
    "assets/reviewed-cases/green-shirt-home/pants-reference.jpg",
    "assets/reviewed-cases/green-shirt-home/before-after.jpg",
    "assets/reviewed-cases/green-shirt-home/six-poses.jpg",
)
REVIEWED_FILES = {"reviewed-cases.html", "reviewed-cases.json"} | {
    f"assets/reviewed-cases/{case}/look-{pose}.png"
    for case in REVIEWED_CASE_IDS for pose in range(1, 7)
}


def validate_reviewed_cases(gallery: Path) -> list[str]:
    """A fixed publication set; its manifest cannot expand deployment scope."""
    findings = []
    try:
        manifest = json.loads((gallery / "reviewed-cases.json").read_text())
        cases = manifest["cases"]
        if manifest.get("schema_version") != "1.0" or [c["id"] for c in cases] != list(REVIEWED_CASE_IDS):
            raise ValueError("expected six reviewed cases in publication order")
        hashes = []
        for case in cases:
            if case.get("ai_generated") is not True or case.get("status") != "image-draft":
                findings.append(f"{case['id']}: missing AI draft disclosure")
            if case.get("visual_acceptance") not in ("accepted", "pending-human-review"):
                findings.append(f"{case['id']}: invalid visual acceptance")
            if [item["pose"] for item in case["images"]] != list(range(1, 7)):
                raise ValueError(f"{case['id']}: expected fixed six poses")
            for item in case["images"]:
                expected_path = f"assets/reviewed-cases/{case['id']}/look-{item['pose']}.png"
                if item.get("path") != expected_path or item.get("dimensions") != [1024, 1536] or item.get("format") != "PNG":
                    raise ValueError(f"{case['id']}: invalid image path or canvas contract")
                if not all(key in item for key in ("sha256", "bytes")):
                    raise ValueError(f"{expected_path}: missing integrity record")
                hashes.append(item["sha256"])
                findings.extend(_record_findings(gallery / expected_path, item, expected_path))
            if case["id"] == "external-black-leather":
                source = case["input_image"]
                if source.get("path") != EXTERNAL_INPUT or case.get("publication_permission", {}).get("authorized") is not True:
                    raise ValueError("external trial: source path or publication permission invalid")
                if not all(key in source for key in ("sha256", "bytes", "dimensions", "format")):
                    raise ValueError("external trial: missing input integrity record")
                findings.extend(_record_findings(gallery / EXTERNAL_INPUT, source, EXTERNAL_INPUT))
            if case["id"] == "green-shirt-home":
                presentation = case.get("presentation", [])
                if presentation or any((gallery / name).exists() for name in HOME_PRESENTATION_FILES):
                    if [item["path"] for item in presentation] != list(HOME_PRESENTATION_FILES):
                        raise ValueError("home presentation: expected fixed two references and two sharing images")
                    for item in presentation:
                        if not all(key in item for key in ("sha256", "bytes", "dimensions", "format")):
                            raise ValueError("home presentation: missing integrity record")
                        findings.extend(_record_findings(gallery / item["path"], item, item["path"]))
            if case["id"] == "black-jacket-office":
                source = case["input_image"]
                external = next(c for c in cases if c["id"] == "external-black-leather")
                if source.get("path") != OFFICE_INPUT or case.get("publication_permission", {}).get("authorized") is not True:
                    raise ValueError("office case: source path or publication permission invalid")
                findings.extend(_record_findings(gallery / OFFICE_INPUT, source, OFFICE_INPUT))
                if source.get("sha256") != external["input_image"]["sha256"]:
                    raise ValueError("office comparison: same real input required")
                if (case.get("source_coverage", {}).get("real_rear") != "missing"
                        or case.get("pose_exception", {}).get("slot") != 6
                        or case["images"][-1].get("original_pose") != "BACK_TURN_GLANCE"
                        or case["images"][-1].get("actual_pose") != "FRONT_RELAXED_STANDING"
                        or case.get("pose_exception", {}).get("rear_construction_verified") is not False):
                    raise ValueError("office case: missing rear-source replacement disclosure")
        if len(set(hashes)) != len(REVIEWED_CASE_IDS) * 6:
            findings.append("reviewed cases: expected 36 distinct image hashes")
    except (OSError, ValueError, TypeError, KeyError) as error:
        findings.append(f"invalid or missing reviewed case manifest: {error}")
    return findings


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.refs = []
        self.links = []
        self.linked_images = []
        self.anchor = None
        self.feed(text)
        for reference in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text):
            self.refs.append(("css", "src", reference))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a":
            self.anchor = attrs.get("href")
            if self.anchor:
                self.links.append(self.anchor)
        for name in ("href", "src", "poster"):
            if attrs.get(name):
                reference_tag = "link:canonical" if tag == "link" and attrs.get("rel") == "canonical" else tag
                self.refs.append((reference_tag, name, attrs[name]))
        if attrs.get("srcset"):
            for candidate in attrs["srcset"].split(","):
                self.refs.append((tag, "src", candidate.strip().split()[0]))
        if tag == "img" and self.anchor:
            self.linked_images.append((self.anchor, attrs.get("src")))

    def handle_endtag(self, tag):
        if tag == "a":
            self.anchor = None


def _local_target(gallery: Path, page: Path, reference: str):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme == "https" and parsed.netloc:
            return None
        raise ValueError(f"unsupported URL scheme: {reference}")
    relative = unquote(parsed.path)
    if relative.startswith("/") or "\\" in relative:
        raise ValueError(f"reference escapes deployment scope: {reference}")
    target = (page.parent / relative).resolve() if relative else page.resolve()
    if not target.is_relative_to(gallery.resolve()):
        raise ValueError(f"reference escapes deployment scope: {reference}")
    if target.is_dir():
        target /= "index.html"
    return target, unquote(parsed.fragment)


def _record_findings(path: Path, expected: dict, label: str, *, image: bool = True) -> list[str]:
    if not path.is_file():
        return [f"missing asset: {label}"]
    findings = []
    if assets.sha256(path) != expected.get("sha256"):
        findings.append(f"{label}: sha256 mismatch")
    try:
        actual = assets.file_info(path, image=image)
        for name in ("bytes", "dimensions", "format"):
            if name in expected and actual.get(name) != expected[name]:
                findings.append(f"{label}: {name} mismatch")
    except ValueError as error:
        findings.append(f"{label}: {error}")
    return findings


def validate_showcase(gallery: Path, *, repo_root: Path | None = None, expected_cases: int = 24, require_brand: bool = False) -> list[str]:
    gallery = gallery.resolve()
    findings = []
    # The API preserves legacy gallery fixtures; the deployment CLI requires
    # the brand manifest. Any gallery carrying brand files is checked as well.
    has_brand = require_brand or (gallery / brand.MANIFEST_PATH).exists() or (gallery / "assets/brand").exists()
    if has_brand:
        findings.extend(brand.validate_brand(gallery, repo_root=repo_root))
    has_reviewed = (gallery / "reviewed-cases.json").exists() or (gallery / "reviewed-cases.html").exists() or (gallery / "assets/reviewed-cases").exists()
    if has_reviewed:
        findings.extend(validate_reviewed_cases(gallery))
    pages = {}
    private_pattern = re.compile(r"(?:/(?:Users|home)/[^\s/]+/|[A-Za-z]:\\(?:Users|Documents and Settings)\\|file://)")
    for name in ("index.html", "compare.html", *(("reviewed-cases.html",) if has_reviewed else ())):
        path = gallery / name
        if not path.is_file():
            findings.append(f"missing page: {name}")
            continue
        pages[path] = Page(path.read_text(encoding="utf-8"))
        duplicates = [key for key, count in Counter(pages[path].ids).items() if count > 1]
        if duplicates:
            findings.append(f"{name}: duplicate IDs: {', '.join(duplicates)}")
    for path in gallery.rglob("*"):
        relative = path.relative_to(gallery).as_posix()
        if path.is_symlink():
            findings.append(f"unsafe deployment symlink: {relative}")
        if path.is_file() and path.suffix in (".html", ".json", ".js", ".css", ".md", ".txt"):
            if private_pattern.search(path.read_text(encoding="utf-8", errors="replace")):
                findings.append(f"private path found in {relative}")
    reference_sources = dict(pages)
    for path in gallery.rglob("*.css"):
        reference_sources[path] = Page(path.read_text(encoding="utf-8"))
    for path, page in reference_sources.items():
        for tag, attribute, reference in page.refs:
            try:
                local = _local_target(gallery, path, reference)
                if local is None:
                    if tag not in ("a", "link:canonical") or attribute != "href":
                        findings.append(f"{path.name}: embedded asset must be local: {reference}")
                    continue
                target, fragment = local
                if not target.is_file():
                    findings.append(f"{path.name}: missing local target {reference}")
                elif fragment and target.suffix == ".html":
                    linked_page = pages.get(target) or Page(target.read_text(encoding="utf-8"))
                    if fragment not in linked_page.ids:
                        findings.append(f"{path.name}: missing anchor {reference}")
                if attribute in ("src", "poster") and target.is_relative_to(gallery / "images"):
                    findings.append(f"{path.name}: inline original PNG: {reference}")
            except ValueError as error:
                findings.append(f"{path.name}: {error}")
    try:
        rights = assets.load_rights(gallery / "rights.json", expected_cases)
        manifest = json.loads((gallery / "display-manifest.json").read_text())
        if not isinstance(manifest, dict):
            raise ValueError("display manifest must be an object")
        primary = json.loads((gallery / "assets/primary/rights.json").read_text())
        beige = json.loads((gallery / "assets/beige-outfit-rights.json").read_text())
        copies = assets.authorized_copies(primary, beige)
    except (OSError, ValueError, TypeError, KeyError) as error:
        findings.append(f"invalid or missing showcase manifest/rights: {error}")
        return findings
    if (manifest.get("schema_version") != "1.0" or manifest.get("gallery_path") != assets.GALLERY_PATH
            or manifest.get("rights_path") != "rights.json"
            or manifest.get("rights_sha256") != assets.sha256(gallery / "rights.json")):
        findings.append("display manifest version, gallery path or rights sha256 mismatch")
    originals = {}
    expected_records = {}
    for case in rights["cases"]:
        style = case["style"]
        comparison = pages.get(gallery / "compare.html")
        if comparison and style not in comparison.ids:
            findings.append(f"compare.html: missing style ID {style}")
        for item in case["images"]:
            original = f"images/{style}/{item['side']}.png"
            output = f"display/{style}/{item['side']}.webp"
            originals[original] = item
            findings.extend(_record_findings(gallery / original, {**item, "format": "PNG"}, original))
            expected_records[output] = {
                "kind": "comparison-display", "style": style, "side": item["side"], "route": item["route"],
                "rights_path": "rights.json", "source_path": f"{assets.GALLERY_PATH}/{original}",
                "derivation": assets.DISPLAY_PARAMETERS,
            }
            if comparison:
                matches = [link for link in comparison.links if unquote(urlsplit(link).path) == original]
                if len(matches) != 1:
                    findings.append(f"compare.html: expected one original result link: {original}")
                linked = [(unquote(urlsplit(link).path), unquote(urlsplit(src or '').path)) for link, src in comparison.linked_images]
                if (original, output) not in linked:
                    findings.append(f"compare.html: original link must wrap matching display image: {original}")
    for copy in copies:
        output = copy["output_path"]
        findings.extend(_record_findings(gallery / output, copy, output))
        expected_records[output] = {
            "kind": "authorized-copy", "rights_path": copy["rights_path"],
            "source_path": copy["source_path"], "derivation": assets.COPY_PARAMETERS,
        }
    for source, output in (
        (f"{assets.PRIMARY_PATH}/rights.json", "assets/primary/rights.json"),
        (f"{assets.BEIGE_PATH}/rights.json", "assets/beige-outfit-rights.json"),
    ):
        expected_records[output] = {"kind": "rights-copy", "source_path": source, "derivation": assets.COPY_PARAMETERS}
    seen = set()
    records = manifest.get("assets", [])
    if not isinstance(records, list):
        findings.append("manifest assets must be an array")
        records = []
    for record in records:
        try:
            output = assets.relative_path(record["output"]["path"])
            source_path = assets.relative_path(record["source"]["path"])
            if output in seen or output not in expected_records:
                raise ValueError(f"duplicate or unexpected manifest output: {output}")
            seen.add(output)
            expected = expected_records[output]
            for name, value in expected.items():
                actual = source_path if name == "source_path" else record.get(name)
                if actual != value:
                    findings.append(f"{output}: manifest {name} mismatch")
            is_image = expected["kind"] != "rights-copy"
            for section in ("source", "output"):
                required = ("sha256", "bytes", "dimensions", "format") if is_image else ("sha256", "bytes")
                for name in required:
                    if name not in record[section]:
                        findings.append(f"{output}: manifest {section} missing {name}")
            findings.extend(_record_findings(gallery / output, record["output"], output, image=is_image))
            if expected["kind"] == "comparison-display":
                local_source = source_path.removeprefix(f"{assets.GALLERY_PATH}/")
                findings.extend(_record_findings(gallery / local_source, record["source"], local_source))
                original = originals.get(local_source)
                if original:
                    if record["output"].get("dimensions") != assets.expected_dimensions(original["dimensions"]):
                        findings.append(f"{output}: aspect ratio or no-upscale contract violated")
                    if record["output"].get("format") != "WEBP":
                        findings.append(f"{output}: expected WEBP format")
            else:
                for name in ("sha256", "bytes", "dimensions", "format"):
                    if record["source"].get(name) != record["output"].get(name):
                        findings.append(f"{output}: byte-identical copy {name} mismatch")
            if repo_root is not None:
                findings.extend(_record_findings(repo_root / source_path, record["source"], source_path, image=is_image))
        except (KeyError, TypeError, ValueError) as error:
            findings.append(f"invalid manifest asset: {error}")
    for missing in sorted(set(expected_records) - seen):
        findings.append(f"missing manifest asset: {missing}")
    allowed_files = {
        "index.html", "compare.html", "home.css", "home.js", "compare.css", "compare.js", "brand.css", "prompt-copy.js",
        "rights.json", "display-manifest.json", *originals, *expected_records,
    }
    if has_brand:
        # Fixed code-owned contract: a manifest cannot authorize extra files.
        allowed_files.update({brand.MANIFEST_PATH, *brand.BRAND_FILES})
    if has_reviewed:
        allowed_files.update(REVIEWED_FILES)
        allowed_files.add(EXTERNAL_INPUT)
        allowed_files.add(OFFICE_INPUT)
        allowed_files.update(HOME_PRESENTATION_FILES)
    # The already-published input remains a byte-identical alias for old links.
    legacy_input = gallery / "inputs/beige-outfit.jpg"
    if legacy_input.exists():
        allowed_files.add("inputs/beige-outfit.jpg")
        findings.extend(_record_findings(legacy_input, copies[-1], "inputs/beige-outfit.jpg"))
    for path in gallery.rglob("*"):
        if path.is_file() and path.relative_to(gallery).as_posix() not in allowed_files:
            findings.append(f"unexpected deployment file: {path.relative_to(gallery).as_posix()}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gallery", type=Path, default=Path(__file__).resolve().parents[1] / assets.GALLERY_PATH)
    parser.add_argument("--repo-root", type=Path, help="Also check provenance against repository source files")
    args = parser.parse_args()
    findings = validate_showcase(args.gallery, repo_root=args.repo_root, require_brand=True)
    if findings:
        print("FAIL: showcase validation")
        for finding in findings:
            print(f"- {finding}")
        return 1
    reviewed = "; 36 reviewed-case PNGs and authorized same-input records" if (args.gallery / "reviewed-cases.json").exists() else ""
    print(f"PASS: 24 styles, 48 original links, 48 WebP derivatives, 12 authorized demo images{reviewed}; local references, rights records, licensed brand assets and deployment scope verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
