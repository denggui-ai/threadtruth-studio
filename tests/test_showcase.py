"""Small real image fixtures exercise the published showcase boundary."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import check_showcase, showcase_assets


ROOT = Path(__file__).resolve().parents[1]
GALLERY = Path("gallery/style24-comparison-20260929")
PRIMARY = Path("docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold")
BEIGE = Path("docs/demo/preview-sources/beige-blazer-denim-outfit")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def image_record(path, size=(32, 48)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (171, 139, 117)).save(path)
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "dimensions": list(size),
        "bytes": path.stat().st_size,
    }


class ShowcaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "repo"
        self.gallery = self.root / GALLERY
        self.cases = []
        # Reversed A/B routes are intentional: side does not identify the host.
        for style, routes in (("first-style", ("native", "web")), ("second-style", ("web", "native"))):
            images = []
            for side, route in zip(("A", "B"), routes):
                record = image_record(self.gallery / "images" / style / f"{side}.png")
                images.append({"side": side, "route": route, "sha256": record["sha256"], "dimensions": record["dimensions"]})
            self.cases.append({
                "style": style, "status": "published", "label": style,
                "reason": "Maintainer approved research display",
                "source_page": "https://example.org/photo", "author_record": "Author",
                "license": "Demo only", "source_sha256": "1" * 64,
                "identity_sha256": "2" * 64, "images": images,
            })
        self.rights = {"scope": "published research gallery", "review_date": "2026-09-29",
                       "counts": {"cases": 2, "local_images": 4, "held_pairs": 0,
                                  "published_pairs": 2, "published_images": 4}, "cases": self.cases}
        write_json(self.gallery / "rights.json", self.rights)
        primary = json.loads((ROOT / PRIMARY / "rights.json").read_text())
        for asset in primary["assets"] + [primary["hero"]]:
            info = image_record(self.root / PRIMARY / asset["path"])
            asset["public_sha256" if "public_sha256" in asset else "sha256"] = info["sha256"]
            asset.update(bytes=info["bytes"], width=32, height=48)
        write_json(self.root / PRIMARY / "rights.json", primary)
        beige = json.loads((ROOT / BEIGE / "rights.json").read_text())
        info = image_record(self.root / BEIGE / "source.jpg")
        beige["public_asset"].update(sha256=info["sha256"], bytes=info["bytes"], width=32, height=48)
        write_json(self.root / BEIGE / "rights.json", beige)
        self.write_pages()

    def write_pages(self):
        cards = []
        for case in self.cases:
            cards.append(f'<section id="{case["style"]}">')
            for side in ("A", "B"):
                stem = f'{case["style"]}/{side}'
                cards.append(f'<a href="images/{stem}.png"><img src="display/{stem}.webp"></a>')
            cards.append("</section>")
        (self.gallery / "compare.html").write_text("".join(cards))
        (self.gallery / "index.html").write_text(
            '<main id="begin"><a href="compare.html?mode=all#first-style">Compare</a>'
            '<a href="#begin">Home</a><a href="https://example.org/a?x=1#outside">Source</a>'
            '<link rel="canonical" href="https://example.org/showcase/">'
            '<img src="assets/primary/hero.jpg"></main>'
        )

    def build(self):
        return showcase_assets.build_assets(self.root)

    def findings(self, gallery=None, repo_root=None):
        return check_showcase.validate_showcase(gallery or self.gallery, repo_root=repo_root, expected_cases=2)

    def test_builder_preserves_per_case_routes_and_original_hashes(self):
        original = (self.gallery / "images/second-style/A.png").read_bytes()
        manifest = self.build()
        record = next(x for x in manifest["assets"] if x.get("style") == "second-style" and x.get("side") == "A")
        self.assertEqual(record["route"], "web")
        self.assertEqual(record["source"]["path"], f"{GALLERY}/images/second-style/A.png")
        self.assertEqual(record["source"]["sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual((self.gallery / "images/second-style/A.png").read_bytes(), original)
        self.assertEqual(self.findings(repo_root=self.root), [])

    def test_display_resize_preserves_aspect_and_never_upscales(self):
        record = image_record(self.gallery / "images/first-style/A.png", (1600, 2400))
        self.rights["cases"][0]["images"][0].update(sha256=record["sha256"], dimensions=[1600, 2400])
        write_json(self.gallery / "rights.json", self.rights)
        self.build()
        with Image.open(self.gallery / "display/first-style/A.webp") as large:
            self.assertEqual(large.size, (960, 1440))
        with Image.open(self.gallery / "display/first-style/B.webp") as small:
            self.assertEqual(small.size, (32, 48))

    def test_builder_is_deterministic_and_source_jpegs_are_byte_identical(self):
        self.build()
        first = (self.gallery / "display-manifest.json").read_bytes()
        self.build()
        self.assertEqual((self.gallery / "display-manifest.json").read_bytes(), first)
        self.assertEqual((self.gallery / "assets/primary/hero.jpg").read_bytes(), (self.root / PRIMARY / "hero.jpg").read_bytes())
        self.assertEqual((self.gallery / "assets/beige-outfit.jpg").read_bytes(), (self.root / BEIGE / "source.jpg").read_bytes())

    def test_builder_rejects_nonpublished_or_duplicate_sides(self):
        for kind in ("status", "side"):
            with self.subTest(kind=kind):
                invalid = json.loads(json.dumps(self.rights))
                if kind == "status":
                    invalid["cases"][0]["status"] = "held"
                else:
                    invalid["cases"][0]["images"][1]["side"] = "A"
                write_json(self.gallery / "rights.json", invalid)
                with self.assertRaises(ValueError):
                    self.build()

    def test_builder_rejects_source_hash_mismatch_before_writing_outputs(self):
        self.rights["cases"][0]["images"][0]["sha256"] = "0" * 64
        write_json(self.gallery / "rights.json", self.rights)
        with self.assertRaisesRegex(ValueError, "sha256"):
            self.build()
        self.assertFalse((self.gallery / "display").exists())

    def test_extracted_deploy_directory_is_self_contained(self):
        self.build()
        deployed = self.root.parent / "deploy"
        shutil.copytree(self.gallery, deployed)
        shutil.rmtree(self.root)
        self.assertEqual(self.findings(deployed), [])

    def test_missing_or_corrupt_asset_is_reported(self):
        self.build()
        target = self.gallery / "display/first-style/A.webp"
        target.unlink()
        self.assertTrue(any("missing" in x.lower() for x in self.findings()))
        target.write_bytes(b"not an image")
        findings = self.findings()
        self.assertTrue(any("sha256" in x for x in findings))
        self.assertTrue(any("image" in x.lower() for x in findings))

    def test_bad_local_targets_and_fragments_are_reported_but_https_is_allowed(self):
        self.build()
        self.assertEqual(self.findings(), [])
        with (self.gallery / "index.html").open("a") as page:
            page.write('<a href="compare.html?x=1#unknown">Bad anchor</a><img src="assets/missing.jpg">')
        findings = self.findings()
        self.assertTrue(any("unknown" in x for x in findings))
        self.assertTrue(any("missing.jpg" in x for x in findings))

    def test_external_citations_are_allowed_but_embedded_assets_must_be_local(self):
        self.build()
        self.assertEqual(self.findings(), [])
        with (self.gallery / "index.html").open("a") as page:
            page.write('<img src="https://example.org/unapproved.jpg"><script src="https://example.org/code.js"></script>')
        findings = self.findings()
        self.assertTrue(any("unapproved.jpg" in finding for finding in findings))
        self.assertTrue(any("code.js" in finding for finding in findings))

    def test_local_reference_cannot_escape_deploy_directory(self):
        self.build()
        (self.root / "outside.jpg").write_bytes(b"outside")
        with (self.gallery / "index.html").open("a") as page:
            page.write('<img src="../../outside.jpg"><a href="file:///private/demo">bad</a>')
        findings = self.findings()
        self.assertTrue(any("escape" in x for x in findings))
        self.assertTrue(any("scheme" in x for x in findings))

    def test_deployed_stylesheets_and_scripts_are_allowed_but_css_urls_are_checked(self):
        self.build()
        (self.gallery / "home.css").write_text('main { background-image: url("assets/primary/hero.jpg"); }')
        (self.gallery / "home.js").write_text("document.documentElement.dataset.ready = 'true';")
        with (self.gallery / "index.html").open("a") as page:
            page.write('<link rel="stylesheet" href="home.css"><script src="home.js"></script>')
        self.assertEqual(self.findings(), [])
        (self.gallery / "home.css").write_text('main { background-image: url("assets/absent.jpg"); }')
        self.assertTrue(any("absent.jpg" in x for x in self.findings()))

    def test_missing_style_original_link_and_inline_original_are_rejected(self):
        self.build()
        path = self.gallery / "compare.html"
        path.write_text(path.read_text().replace('id="first-style"', 'id="wrong-style"').replace('href="images/first-style/A.png"', 'href="rights.json"').replace('src="display/first-style/B.webp"', 'src="images/first-style/B.png"'))
        findings = self.findings()
        self.assertTrue(any("style" in x for x in findings))
        self.assertTrue(any("original" in x for x in findings))
        self.assertTrue(any("inline" in x for x in findings))

    def test_manifest_route_or_derivation_changes_are_rejected(self):
        manifest = self.build()
        manifest["assets"][0]["route"] = "wrong"
        manifest["assets"][0]["derivation"]["crop"] = True
        write_json(self.gallery / "display-manifest.json", manifest)
        findings = self.findings()
        self.assertTrue(any("route" in x for x in findings))
        self.assertTrue(any("derivation" in x for x in findings))

    def test_manifest_cannot_omit_copied_image_dimensions(self):
        manifest = self.build()
        record = next(item for item in manifest["assets"] if item["kind"] == "authorized-copy")
        del record["source"]["dimensions"]
        del record["output"]["dimensions"]
        write_json(self.gallery / "display-manifest.json", manifest)
        self.assertTrue(any("dimensions" in finding for finding in self.findings()))

    def test_malformed_rights_document_is_a_reported_validation_failure(self):
        self.build()
        write_json(self.gallery / "rights.json", [])
        self.assertTrue(any("rights" in finding for finding in self.findings()))

    def test_private_paths_and_unexpected_deployment_files_are_rejected(self):
        self.build()
        (self.gallery / "internal.py").write_text("print('not public')")
        with (self.gallery / "index.html").open("a") as page:
            page.write("/" + "Users/" + "fixture/private")
        findings = self.findings()
        self.assertTrue(any("private" in x for x in findings))
        self.assertTrue(any("deployment" in x for x in findings))

    def test_authorization_revocation_is_rejected_in_repository_mode(self):
        self.build()
        path = self.root / PRIMARY / "rights.json"
        record = json.loads(path.read_text())
        record["source_rights"]["public_use_authorized"] = False
        write_json(path, record)
        self.assertTrue(self.findings(repo_root=self.root))

    def test_cli_refuses_repository_root_as_deploy_scope(self):
        self.build()
        result = subprocess.run([sys.executable, str(ROOT / "tools/check_showcase.py"), "--gallery", str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("index.html", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
