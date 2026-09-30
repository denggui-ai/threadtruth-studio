"""Regression checks for the fixed, local-only brand deployment boundary."""

import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from PIL import Image

from tools import brand_assets


class BrandAssetsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.gallery = Path(temporary.name)
        for name in brand_assets.TEXT_FILES:
            (self.gallery / name).write_text("裁光 ThreadTruthStudio 已复制 ş")
        self.font_dir = self.gallery / "assets/brand/fonts"
        self.font_dir.mkdir(parents=True)
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        for key, source in brand_assets.FONT_SPECS.items():
            chars = brand_assets.required_codepoints(self.gallery)
            if key == "manrope":
                chars = {value for value in chars if value < 0x3000}
            else:
                chars.discard(ord("ş"))
            builder = FontBuilder(1000, isTTF=True)
            order = [".notdef"] + [f"u{value:X}" for value in sorted(chars)]
            builder.setupGlyphOrder(order)
            builder.setupCharacterMap({value: f"u{value:X}" for value in chars})
            builder.setupGlyf({name: TTGlyphPen(None).glyph() for name in order})
            builder.setupHorizontalMetrics({name: (1000, 0) for name in order})
            builder.setupHorizontalHeader(ascent=800, descent=-200)
            builder.setupNameTable({"familyName": source["family"], "styleName": "Regular"})
            builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
            builder.setupPost()
            builder.setupFvar([("wght", source["weights"][0], source["weights"][0], source["weights"][1], "Weight")], [])
            builder.font.flavor = "woff2"
            builder.save(self.gallery / source["output"])
            (self.gallery / source["license_output"]).write_text("Copyright Fixture. SIL OPEN FONT LICENSE Version 1.1")
        for path in brand_assets.SVG_PATHS:
            (self.gallery / path).write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M0 0L10 10"/></svg>')
        for path in brand_assets.OG_PATHS:
            Image.new("RGB", (1200, 630), "white").save(self.gallery / path)
        self.sources = {}
        for key, spec in brand_assets.FONT_SPECS.items():
            self.sources[key] = brand_assets.source_record(key, "1" * 40, "2" * 64, brand_assets.sha256(self.gallery / spec["license_output"]))
        self.refresh()

    def refresh(self):
        self.manifest = brand_assets.build_manifest(self.gallery, self.sources)
        (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))

    def findings(self):
        return brand_assets.validate_brand(self.gallery)

    def test_valid_local_brand_is_self_contained(self):
        self.assertEqual(self.findings(), [])

    def source_cache(self):
        from fontTools.ttLib import TTFont
        source_dir = self.gallery / "source-cache"
        source_dir.mkdir()
        sources = {}
        for key, spec in brand_assets.FONT_SPECS.items():
            font = TTFont(self.gallery / spec["output"])
            font.flavor = None
            font.save(source_dir / spec["filename"])
            license_path = source_dir / f"{key}-OFL.txt"
            license_path.write_bytes((self.gallery / spec["license_output"]).read_bytes())
            sources[key] = brand_assets.source_record(key, "1" * 40, brand_assets.sha256(source_dir / spec["filename"]), brand_assets.sha256(license_path))
        (source_dir / "sources.json").write_text(json.dumps(sources))
        return source_dir, sources

    def build_fixture_fonts(self, source_dir):
        # Tiny fixtures have no STAT/gvar tables; exercise the real subsetting
        # and saving stages while leaving upstream instancing/outline work out.
        with patch("fontTools.varLib.instancer.instantiateVariableFont", side_effect=lambda font, *args, **kwargs: font), patch.object(brand_assets, "_outline_svg"):
            brand_assets.build_brand(self.gallery, source_dir)

    def test_builder_retains_latin_character_missing_from_noto(self):
        source_dir, sources = self.source_cache()
        self.build_fixture_fonts(source_dir)
        brand_assets.write_manifest(self.gallery, sources)
        self.assertEqual(self.findings(), [])

    def test_font_build_preserves_template_drift_until_cover_is_rendered(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repo = Path(temporary.name) / "repo"
        gallery = repo / brand_assets.GALLERY_PATH
        shutil.copytree(self.gallery, gallery)
        self.gallery = gallery
        for name in brand_assets.SOURCE_TEMPLATES:
            template = repo / name
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("<p>cover composition</p>")
        source_dir, sources = self.source_cache()
        brand_assets.write_manifest(gallery, sources)
        manifest_before = (gallery / brand_assets.MANIFEST_PATH).read_bytes()
        covers_before = {name: (gallery / name).read_bytes() for name in brand_assets.OG_PATHS}
        self.assertEqual(brand_assets.validate_brand(gallery, repo_root=repo), [])

        # A template edit has not yet been rendered into the existing PNG.
        (repo / brand_assets.SOURCE_TEMPLATES[0]).write_text("<p>updated cover composition</p>")
        self.assertTrue(any("template sha256 mismatch" in finding for finding in brand_assets.validate_brand(gallery, repo_root=repo)))
        self.build_fixture_fonts(source_dir)

        # Rebuilding fonts cannot certify that a stale cover matches its source.
        self.assertTrue(any("template sha256 mismatch" in finding for finding in brand_assets.validate_brand(gallery, repo_root=repo)))
        self.assertEqual((gallery / brand_assets.MANIFEST_PATH).read_bytes(), manifest_before)
        self.assertEqual({name: (gallery / name).read_bytes() for name in brand_assets.OG_PATHS}, covers_before)

    def test_corrupt_hash_is_reported(self):
        (self.gallery / brand_assets.SVG_PATHS[0]).write_text('<svg/>')
        self.assertTrue(any("sha256" in finding for finding in self.findings()))

    def test_missing_license_is_reported(self):
        (self.gallery / brand_assets.FONT_SPECS["manrope"]["license_output"]).unlink()
        self.assertTrue(any("missing" in finding and "OFL" in finding for finding in self.findings()))

    def test_manifest_cannot_allow_extra_file_or_traversal(self):
        for path in ("assets/brand/extra.js", "../outside.txt"):
            with self.subTest(path=path):
                self.refresh()
                self.manifest["assets"].append({"output": {"path": path}})
                (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))
                self.assertTrue(any("unexpected" in finding or "escapes" in finding for finding in self.findings()))

    def test_svg_active_content_and_external_links_are_rejected_even_with_refreshed_hash(self):
        for content in ('<image href="https://example.com/a.png"/>', '<script>alert(1)</script>', '<path onload="alert(1)"/>', '<path fill="url(https://example.com/x)"/>', r'<path fill="u\72l(//example.com/x)"/>'):
            with self.subTest(content=content):
                (self.gallery / brand_assets.SVG_PATHS[0]).write_text(f'<svg xmlns="http://www.w3.org/2000/svg">{content}</svg>')
                self.refresh()
                self.assertTrue(any("unsafe SVG" in finding for finding in self.findings()))

    def test_svg_processing_instruction_cannot_load_remote_stylesheet(self):
        path = self.gallery / brand_assets.SVG_PATHS[0]
        path.write_text('<?xml-stylesheet type="text/css" href="https://example.org/style.css"?>' + path.read_text())
        self.refresh()
        self.assertTrue(any("unsafe SVG" in finding for finding in self.findings()))

    def test_og_dimensions_are_checked_independently_of_manifest(self):
        Image.new("RGB", (600, 315), "white").save(self.gallery / brand_assets.OG_PATHS[0])
        self.refresh()
        self.assertTrue(any("1200x630" in finding for finding in self.findings()))

    def test_og_template_text_is_included_in_subset_coverage(self):
        repo = self.gallery / "repo"
        template = repo / brand_assets.SOURCE_TEMPLATES[0]
        template.parent.mkdir(parents=True)
        template.write_text("龘")
        self.assertIn(ord("龘"), brand_assets.required_codepoints(repo / brand_assets.GALLERY_PATH))

    def test_repository_check_binds_og_template_hash(self):
        repo = self.gallery / "repo"
        for record in self.manifest["assets"]:
            if record["kind"] == "share-cover":
                template = repo / record["source_template"]
                template.parent.mkdir(parents=True, exist_ok=True)
                template.write_text("cover composition")
                record["source_template_sha256"] = brand_assets.sha256(template)
        (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))
        self.assertEqual(brand_assets.validate_brand(self.gallery, repo_root=repo), [])
        (repo / brand_assets.SOURCE_TEMPLATES[0]).write_text("changed layout")
        self.assertTrue(any("template sha256 mismatch" in finding for finding in brand_assets.validate_brand(self.gallery, repo_root=repo)))

    def test_new_dynamic_copy_requires_glyph_refresh(self):
        (self.gallery / "prompt-copy.js").write_text('const feedback = "新增罕字龘";')
        self.assertTrue(any("missing glyphs" in finding and "U+9F98" in finding for finding in self.findings()))

    def test_escaped_dynamic_copy_and_html_entities_require_real_glyphs(self):
        for filename, text in (("prompt-copy.js", r'const feedback = "\u9f98";'), ("index.html", "&#x9f98;")):
            with self.subTest(filename=filename):
                (self.gallery / filename).write_text(text)
                self.assertTrue(any("missing glyphs" in finding and "U+9F98" in finding for finding in self.findings()))

    def test_asset_provenance_cannot_be_silently_relabelled(self):
        self.manifest["assets"][0]["source"] = "unlicensed-external-image"
        (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))
        self.assertTrue(any("provenance" in finding for finding in self.findings()))

    def test_woff2_magic_and_real_cmap_are_checked(self):
        (self.gallery / brand_assets.FONT_SPECS["manrope"]["output"]).write_bytes(b"wOF2not-a-font")
        # A self-consistent hash cannot turn corrupt font data into a font.
        for record in self.manifest["assets"]:
            if record["output"]["path"] == brand_assets.FONT_SPECS["manrope"]["output"]:
                record["output"].update(brand_assets.file_info(self.gallery / record["output"]["path"], image=False))
        (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))
        self.assertTrue(any("invalid font" in finding for finding in self.findings()))

    def test_unofficial_source_and_license_hash_tampering_are_rejected(self):
        self.manifest["sources"]["manrope"]["font_url"] = "https://example.org/font.ttf"
        self.manifest["sources"]["manrope"]["license_sha256"] = "0" * 64
        (self.gallery / brand_assets.MANIFEST_PATH).write_text(json.dumps(self.manifest))
        findings = self.findings()
        self.assertTrue(any("source" in finding for finding in findings))
        self.assertTrue(any("license" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
