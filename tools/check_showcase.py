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
except ImportError:
    import showcase_assets as assets


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


def validate_showcase(gallery: Path, *, repo_root: Path | None = None, expected_cases: int = 24) -> list[str]:
    gallery = gallery.resolve()
    findings = []
    pages = {}
    private_pattern = re.compile(r"(?:/(?:Users|home)/[^\s/]+/|[A-Za-z]:\\(?:Users|Documents and Settings)\\|file://)")
    for name in ("index.html", "compare.html"):
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
        "index.html", "compare.html", "home.css", "home.js", "compare.css", "compare.js",
        "rights.json", "display-manifest.json", *originals, *expected_records,
    }
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
    findings = validate_showcase(args.gallery, repo_root=args.repo_root)
    if findings:
        print("FAIL: showcase validation")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("PASS: 24 styles, 48 original links, 48 WebP derivatives, 12 authorized demo images; local references, rights and deployment scope verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
