"""Keep the released beta.4 gallery immutable while current prompts evolve."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = "beige-blazer-denim-outfit-24-v1"
FIXTURE = f"tests/fixtures/{COLLECTION}-beta4.sha256.json"


class FrozenOutfitPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("docs/demo", "skills/threadtruth-studio/references"):
            shutil.copytree(ROOT / name, self.root / name)
        shutil.rmtree(self.root / "docs/demo/style-previews/white-vest-24-v1")
        fixture = self.root / FIXTURE
        fixture.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / FIXTURE, fixture)
        self.public = self.root / "docs/demo/style-previews" / COLLECTION
        spec = importlib.util.spec_from_file_location("style_preview", ROOT / "tools/style_preview.py")
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_released_bytes_are_valid_historical_evidence_but_not_current_prompt_evidence(self):
        manifest = json.loads((ROOT / FIXTURE).read_text())
        self.assertEqual(len(manifest), 75)
        for name, expected in manifest.items():
            data = (self.public / name).read_bytes()
            self.assertEqual(expected, {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        self.assertEqual(self.m.validate_public_previews(self.root), [])
        record = self.m.read_json(self.public / "evidence.json")
        with self.assertRaisesRegex(ValueError, "prompt is not reproducible"):
            self.m._check_plan(self.root, record)

    def test_media_record_and_disclosures_cannot_be_changed_or_removed(self):
        for name in ("american-street.jpg", "evidence.json", "README.md", "index.html"):
            path = self.public / name
            original = path.read_bytes()
            with self.subTest(name=name, change="tamper"):
                path.write_bytes(original + b"\n")
                self.assertIn("asset mismatch", " ".join(self.m.validate_public_previews(self.root)))
                path.write_bytes(original)
            with self.subTest(name=name, change="remove"):
                path.unlink()
                self.assertTrue(self.m.validate_public_previews(self.root))
                path.write_bytes(original)
        (self.public / "extra.txt").write_text("unregistered")
        self.assertIn("file set mismatch", " ".join(self.m.validate_public_previews(self.root)))

    def test_frozen_validation_still_checks_the_authoritative_source_bytes(self):
        source = self.root / "docs/demo/preview-sources/beige-blazer-denim-outfit/source.jpg"
        source.write_bytes(b"changed source")
        self.assertTrue(self.m.validate_public_previews(self.root))

    def test_other_schema_five_collections_do_not_gain_the_frozen_exemption(self):
        renamed = self.public.with_name("another-v5-collection")
        self.public.rename(renamed)
        record = self.m.read_json(renamed / "evidence.json")
        record["run_id"] = renamed.name
        for batch in record["batches"]:
            batch["run_id"] = renamed.name
        self.m.write_json(renamed / "evidence.json", record)
        self.assertIn("prompt is not reproducible", " ".join(self.m.validate_public_previews(self.root)))

    def test_frozen_run_id_cannot_be_prepared_or_mutated(self):
        with self.assertRaisesRegex(ValueError, "frozen public evidence"):
            self.m.prepare(self.root, COLLECTION, "beige-blazer-denim-outfit")
        local = self.m.run_dir(self.root, COLLECTION)
        self.assertFalse(local.exists())
        local.mkdir(parents=True)
        shutil.copyfile(self.public / "evidence.json", local / "evidence.json")
        before = (local / "evidence.json").read_bytes()
        for mutate in (
            lambda: self.m.prepare(self.root, COLLECTION),
            lambda: self.m.register_batch(self.root, COLLECTION, {}),
            lambda: self.m.ingest(self.root, COLLECTION, "american-street", Path("missing-image"), {}),
            lambda: self.m.compose(self.root, COLLECTION, "american-street", {}, Path("missing-font")),
            lambda: self.m.approve(self.root, COLLECTION, "american-street", {}),
            lambda: self.m.promote(self.root, COLLECTION),
        ):
            with self.assertRaisesRegex(ValueError, "frozen public evidence"):
                mutate()
        self.assertEqual((local / "evidence.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
