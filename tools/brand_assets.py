#!/usr/bin/env python3
"""Fetch licensed Google Fonts, build local brand assets, or refresh their manifest.

Use an isolated environment with requirements-dev.txt. Source TTFs remain outside
the deployment directory. Re-run build after editing page or script copy; build
never changes the manifest. Render the two 1200x630 OG PNGs from their current
templates before explicitly running manifest. No image originals are edited.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from .showcase_assets import GALLERY_PATH, file_info, relative_path, sha256
except ImportError:
    from showcase_assets import GALLERY_PATH, file_info, relative_path, sha256


MANIFEST_PATH = "brand-assets.json"
TEXT_FILES = ("index.html", "compare.html", "home.css", "compare.css", "brand.css", "home.js", "compare.js", "prompt-copy.js")
BASE_TEXT = "裁光 Caiguang AI Fashion Studio 服饰AI影棚 你的衣服。下一组大片。Your garments. A new perspective. 开始使用 Get started 查看24风格 Explore24styles 已复制 复制失败 请手动复制"
FONT_SPECS = {
    "notosanssc": {"family": "Noto Sans SC", "filename": "NotoSansSC[wght].ttf", "weights": [400, 900],
                   "output": "assets/brand/fonts/noto-sans-sc.woff2", "license_output": "assets/brand/fonts/NotoSansSC-OFL.txt"},
    "manrope": {"family": "Manrope", "filename": "Manrope[wght].ttf", "weights": [400, 800],
                "output": "assets/brand/fonts/manrope.woff2", "license_output": "assets/brand/fonts/Manrope-OFL.txt"},
}
SVG_PATHS = ("assets/brand/wordmark.svg", "assets/brand/favicon.svg")
OG_PATHS = ("assets/brand/og-home.png", "assets/brand/og-compare.png")
BRAND_FILES = frozenset([*SVG_PATHS, *OG_PATHS, *(spec[name] for spec in FONT_SPECS.values() for name in ("output", "license_output"))])
MAX_FONT_BYTES = 500_000
SOURCE_TEMPLATES = ("tools/brand_cards/og-home.html", "tools/brand_cards/og-compare.html")


def _repository_root(gallery: Path) -> Path | None:
    gallery = gallery.resolve()
    return gallery.parents[1] if gallery.parts[-2:] == Path(GALLERY_PATH).parts else None


def required_codepoints(gallery: Path) -> set[int]:
    """Conservatively include all page/CSS/JS literals, including dynamic feedback.

    Scan the complete fixed text-file set so edits cannot silently evade subset
    coverage by moving a string between markup and JavaScript.
    """
    text = BASE_TEXT + "".join((gallery / name).read_text(encoding="utf-8") for name in TEXT_FILES if (gallery / name).is_file())
    repository = _repository_root(gallery)
    if repository:
        text += "".join((repository / name).read_text(encoding="utf-8") for name in SOURCE_TEMPLATES if (repository / name).is_file())
    text += html.unescape(text)
    text += "".join(chr(int(value, 16)) for value in re.findall(r"\\u([0-9A-Fa-f]{4})", text))
    return {ord(char) for char in text if char.isprintable()} | set(range(32, 127))


def source_record(key: str, revision: str, font_sha: str, license_sha: str) -> dict:
    spec = FONT_SPECS[key]
    base = f"https://raw.githubusercontent.com/google/fonts/{revision}/ofl/{key}"
    return {"family": spec["family"], "repository": "https://github.com/google/fonts", "revision": revision,
            "font_url": f"{base}/{spec['filename'].replace('[', '%5B').replace(']', '%5D')}",
            "license_url": f"{base}/OFL.txt", "source_sha256": font_sha,
            "license_sha256": license_sha, "license": "OFL-1.1"}


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ThreadTruthStudio-brand-builder"})
    with urllib.request.urlopen(request, timeout=90) as response:
        if not response.url.startswith(("https://raw.githubusercontent.com/", "https://api.github.com/")):
            raise ValueError("font download redirected outside official GitHub hosts")
        return response.read()


def fetch_sources(cache: Path, revision: str | None = None) -> dict:
    if revision is None:
        revision = json.loads(_download("https://api.github.com/repos/google/fonts/commits/main"))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Google Fonts revision must be a full commit SHA")
    cache.mkdir(parents=True, exist_ok=True)
    sources = {}
    for key, spec in FONT_SPECS.items():
        record = source_record(key, revision, "", "")
        font, license_path = cache / spec["filename"], cache / f"{key}-OFL.txt"
        font.write_bytes(_download(record["font_url"]))
        license_path.write_bytes(_download(record["license_url"]))
        if font.read_bytes()[:4] != b"\x00\x01\x00\x00":
            raise ValueError(f"download is not a TrueType font: {key}")
        if "SIL OPEN FONT LICENSE" not in license_path.read_text():
            raise ValueError(f"missing OFL license: {key}")
        sources[key] = source_record(key, revision, sha256(font), sha256(license_path))
    (cache / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")
    return sources


def load_sources(source_dir: Path) -> dict:
    sources = json.loads((source_dir / "sources.json").read_text())
    for key, spec in FONT_SPECS.items():
        for path, field in ((source_dir / spec["filename"], "source_sha256"), (source_dir / f"{key}-OFL.txt", "license_sha256")):
            if sha256(path) != sources[key][field]:
                raise ValueError(f"source cache {field} mismatch: {key}")
    return sources


def font_info(path: Path) -> dict:
    from fontTools.ttLib import TTFont
    if path.read_bytes()[:4] != b"wOF2":
        raise ValueError("invalid font: expected WOFF2 magic")
    with TTFont(path) as font:
        axes = {axis.axisTag: [axis.minValue, axis.maxValue] for axis in font["fvar"].axes} if "fvar" in font else {}
        return {"family": font["name"].getDebugName(1), "weights": axes.get("wght"),
                "codepoints": sorted(font.getBestCmap() or {})}


def _outline_svg(font_path: Path, text: str, output: Path, *, icon: bool = False) -> None:
    from fontTools import subset
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    font = TTFont(font_path, recalcTimestamp=False)
    subsetter = subset.Subsetter()
    subsetter.populate(text=text)
    subsetter.subset(font)
    font = instantiateVariableFont(font, {"wght": 900}, inplace=True)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    paths, advance = [], 0
    for char in text:
        glyph = glyphs[cmap[ord(char)]]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        paths.append(f'<path transform="translate({advance} 0)" d="{pen.getCommands()}"/>')
        advance += glyph.width + (80 if not icon else 0)
    # Font em is 1000. Keep a generous fixed canvas so all outline extrema fit.
    if icon:
        body = '<rect width="1200" height="1200" rx="220" fill="#20211F"/>' + '<g fill="#F7F7F5" transform="translate(100 990) scale(1 -1)">' + "".join(paths) + '</g>'
        viewbox = "0 0 1200 1200"
    else:
        body = '<g fill="#20211F" transform="translate(0 940) scale(1 -1)">' + "".join(paths) + '</g>'
        viewbox = f"0 0 {advance - 80} 1100"
    output.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" role="img" aria-label="{text}">{body}</svg>\n')


def build_brand(gallery: Path, source_dir: Path) -> dict:
    """Build fonts and outlines without certifying or refreshing cover provenance."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    load_sources(source_dir)
    required = required_codepoints(gallery)
    available = set()
    for spec in FONT_SPECS.values():
        with TTFont(source_dir / spec["filename"]) as source_font:
            available.update(source_font.getBestCmap())
    if required - available:
        raise ValueError(f"font sources missing glyphs: {_codes(required - available)}")
    for key, spec in FONT_SPECS.items():
        original = TTFont(source_dir / spec["filename"], recalcTimestamp=False)
        cmap = original.getBestCmap()
        wanted = set(required) if key == "notosanssc" else {code for code in required if code < 0x3000}
        # Noto supplies non-Latin symbols that Manrope does not contain.
        wanted &= set(cmap)
        options = subset.Options()
        options.recalc_timestamp = False
        options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14, 16, 17]
        options.name_legacy = True
        options.name_languages = ["*"]
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=wanted)
        subsetter.subset(original)
        # Subset first: this also avoids spending instancing time on CJK glyphs
        # that are never shipped and preserves composite/ligature closure.
        font = instantiateVariableFont(original, {"wght": (spec["weights"][0], spec["weights"][0], spec["weights"][1])}, inplace=True, updateFontNames=True)
        font.flavor = "woff2"
        output = gallery / spec["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        font.save(output, reorderTables=False)
        if output.stat().st_size > MAX_FONT_BYTES:
            raise ValueError(f"font subset exceeds {MAX_FONT_BYTES} bytes: {output.name}")
        shutil.copyfile(source_dir / f"{key}-OFL.txt", gallery / spec["license_output"])
    original = source_dir / FONT_SPECS["notosanssc"]["filename"]
    _outline_svg(original, "裁光", gallery / SVG_PATHS[0])
    _outline_svg(original, "光", gallery / SVG_PATHS[1], icon=True)
    return {key: file_info(gallery / spec["output"], image=False) for key, spec in FONT_SPECS.items()}


def build_manifest(gallery: Path, sources: dict) -> dict:
    records = []
    for path in sorted(BRAND_FILES):
        record = {"output": {"path": path, **file_info(gallery / path, image=path in OG_PATHS)}, **asset_provenance(path)}
        if record["kind"] == "font":
            record["font"] = font_info(gallery / path)
        repository = _repository_root(gallery)
        if record["kind"] == "share-cover" and repository:
            record["source_template_sha256"] = sha256(repository / record["source_template"])
        records.append(record)
    return {"schema_version": "1.0", "brand": {"zh": "裁光", "en": "Caiguang"}, "sources": sources, "assets": records}


def asset_provenance(path: str) -> dict:
    for key, spec in FONT_SPECS.items():
        if path == spec["output"]:
            return {"kind": "font", "source": key, "derivation": "subset-variable-font-and-encode-woff2"}
        if path == spec["license_output"]:
            return {"kind": "font-license", "source": key}
    if path in SVG_PATHS:
        return {"kind": "glyph-outline", "source": "notosanssc", "text": "裁光" if path == SVG_PATHS[0] else "光", "weight": 900}
    if path in OG_PATHS:
        home = path == OG_PATHS[0]
        return {"kind": "share-cover", "source": "project-layout-and-authorized-showcase-assets" if home else "project-typographic-layout",
                "usage_page": "index.html" if home else "compare.html",
                "source_template": f"tools/brand_cards/og-{'home' if home else 'compare'}.html",
                "source_images": ["display/italian-luxe/A.webp", "assets/beige-outfit.jpg"] if home else [],
                "rights_paths": ["rights.json", "assets/beige-outfit-rights.json"] if home else [], "derivation": "browser-render"}
    raise ValueError(f"unexpected brand path: {path}")


def write_manifest(gallery: Path, sources: dict) -> dict:
    manifest = build_manifest(gallery, sources)
    (gallery / MANIFEST_PATH).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def _codes(codepoints) -> str:
    return ", ".join(f"U+{value:04X}" for value in sorted(codepoints))


def _svg_safe(path: Path) -> bool:
    text = path.read_text()
    if re.search(r"<!DOCTYPE|<!ENTITY|<\?xml-stylesheet", text, re.I):
        return False
    root = ET.fromstring(text)
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in ("svg", "g", "path", "rect", "title", "desc"):
            return False
        for name, value in element.attrib.items():
            name = name.rsplit("}", 1)[-1].lower()
            if name not in {"viewbox", "role", "aria-label", "width", "height", "x", "y", "rx", "ry", "transform", "d", "fill", "fill-rule"}:
                return False
            if "\\" in value or re.search(r"url\s*\(|https?:|data:|javascript:", value, re.I):
                return False
            if name == "fill" and not re.fullmatch(r"#[0-9a-fA-F]{3,8}|none|currentColor", value):
                return False
    return root.tag == "{http://www.w3.org/2000/svg}svg"


def validate_brand(gallery: Path, *, repo_root: Path | None = None) -> list[str]:
    findings = []
    try:
        manifest_path = gallery / MANIFEST_PATH
        if manifest_path.is_symlink() or not manifest_path.resolve().is_relative_to(gallery.resolve()):
            raise ValueError("unsafe brand manifest symlink")
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("schema_version") != "1.0" or manifest.get("brand") != {"zh": "裁光", "en": "Caiguang"}:
            raise ValueError("brand manifest version or names mismatch")
        sources = manifest["sources"]
        if set(sources) != set(FONT_SPECS):
            raise ValueError("brand source allowlist mismatch")
        records = manifest["assets"]
        if not isinstance(records, list):
            raise ValueError("brand assets must be an array")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        return [f"invalid or missing brand manifest: {error}"]
    for key, source in sources.items():
        try:
            expected = source_record(key, source["revision"], source["source_sha256"], source["license_sha256"])
            if source != expected or not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
                findings.append(f"invalid official font source: {key}")
            for field in ("source_sha256", "license_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", source[field]):
                    findings.append(f"invalid source {field}: {key}")
            license_path = gallery / FONT_SPECS[key]["license_output"]
            if license_path.is_symlink() or not license_path.resolve().is_relative_to(gallery.resolve()):
                findings.append(f"unsafe font license path: {key}")
            elif license_path.is_file() and (sha256(license_path) != source["license_sha256"] or "SIL OPEN FONT LICENSE Version 1.1" not in license_path.read_text()):
                findings.append(f"font license content/hash mismatch: {key}")
        except (KeyError, TypeError, ValueError, OSError) as error:
            findings.append(f"invalid font source: {key}: {error}")
    seen, cmaps = set(), {}
    for record in records:
        try:
            relative = relative_path(record["output"]["path"])
            if relative not in BRAND_FILES or relative in seen:
                raise ValueError(f"unexpected or duplicate brand output: {relative}")
            seen.add(relative)
            if any(record.get(name) != value for name, value in asset_provenance(relative).items()):
                findings.append(f"{relative}: brand asset provenance mismatch")
            path = gallery / relative
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(gallery.resolve()):
                raise ValueError(f"missing or unsafe brand file: {relative}")
            actual = file_info(path, image=relative in OG_PATHS)
            for field, value in actual.items():
                if record["output"].get(field) != value:
                    findings.append(f"{relative}: {field} mismatch")
            if relative in SVG_PATHS and not _svg_safe(path):
                findings.append(f"unsafe SVG: {relative}")
            if relative in OG_PATHS and (actual.get("dimensions") != [1200, 630] or actual.get("format") != "PNG"):
                findings.append(f"{relative}: share cover must be PNG 1200x630")
            if relative in OG_PATHS:
                template_sha = record.get("source_template_sha256")
                if template_sha is not None and not re.fullmatch(r"[0-9a-f]{64}", template_sha):
                    findings.append(f"{relative}: invalid source template sha256")
                if repo_root is not None:
                    template = repo_root / asset_provenance(relative)["source_template"]
                    if not template.is_file() or template.is_symlink() or sha256(template) != template_sha:
                        findings.append(f"{relative}: source template sha256 mismatch or missing template")
            for key, spec in FONT_SPECS.items():
                if relative == spec["output"]:
                    try:
                        info = font_info(path)
                        if info != record.get("font") or info["family"] != spec["family"] or info["weights"] != spec["weights"]:
                            findings.append(f"{relative}: font metadata, family or weight range mismatch")
                        cmaps[key] = set(info["codepoints"])
                    except Exception as error:
                        findings.append(f"{relative}: invalid font: {error}")
                    if actual["bytes"] > MAX_FONT_BYTES:
                        findings.append(f"{relative}: font exceeds {MAX_FONT_BYTES} bytes")
        except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as error:
            findings.append(f"invalid brand asset: {error}")
    for missing in sorted(BRAND_FILES - seen):
        findings.append(f"missing brand manifest asset: {missing}")
    if len(cmaps) == len(FONT_SPECS):
        missing = required_codepoints(gallery) - set.union(*cmaps.values())
        if missing:
            findings.append(f"local fonts missing glyphs; rebuild brand subset: {_codes(missing)}")
    if "manrope" in cmaps:
        missing = set(range(32, 127)) - cmaps["manrope"]
        if missing:
            findings.append(f"Manrope missing glyphs: {_codes(missing)}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch", "build", "manifest", "check"))
    parser.add_argument("--gallery", type=Path, default=Path(__file__).resolve().parents[1] / GALLERY_PATH)
    parser.add_argument("--source-dir", "--cache-dir", dest="source_dir", type=Path)
    parser.add_argument("--revision", help="Pinned full google/fonts commit SHA (fetch only)")
    args = parser.parse_args()
    if args.command != "check" and not args.source_dir:
        parser.error("--source-dir is required for fetch/build/manifest")
    try:
        if args.command == "fetch":
            result = fetch_sources(args.source_dir, args.revision)
        elif args.command == "build":
            result = {"fonts": build_brand(args.gallery, args.source_dir), "needs_manifest": True,
                      "next_step": "Render OG PNGs from their current templates, then explicitly run manifest."}
        elif args.command == "manifest":
            result = write_manifest(args.gallery, load_sources(args.source_dir))
            result = {"manifest": MANIFEST_PATH, "assets": len(result["assets"])}
        else:
            findings = validate_brand(args.gallery)
            print("\n".join(findings) if findings else "PASS: local brand assets, licenses, font coverage and covers")
            return bool(findings)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
