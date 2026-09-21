"""Rule edits bind preview evidence by prompt equivalence, not by rule-file hash.

A prepared/approved preview stays valid while the current rules still reproduce its prompt byte for
byte. A rule or pack edit that changes a style's prompt invalidates exactly that style, with a
message naming it, so the maintainer knows which preview must be regenerated under the new rules.
"""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT_BUILD = "skills/threadtruth-studio/references/prompt-build.md"
PACKS = "skills/threadtruth-studio/references/styles"


def module():
    spec = importlib.util.spec_from_file_location("style_preview", ROOT / "tools/style_preview.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class PreviewRulesEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("docs/demo", "skills/threadtruth-studio/references"):
            shutil.copytree(ROOT / name, self.root / name)
        shutil.rmtree(self.root / "docs/demo/style-previews", ignore_errors=True)
        self.m = module()
        self.run = self.m.prepare(self.root, "eq-run", "beige-blazer-denim-outfit")
        self.evidence = self.m.run_dir(self.root, "eq-run") / "evidence.json"

    def test_rule_edit_that_leaves_every_prompt_unchanged_keeps_the_run_valid(self):
        path = self.root / PROMPT_BUILD
        path.write_text(path.read_text(encoding="utf-8") + "\n<!-- documentation-only note -->\n", encoding="utf-8")
        recorded = self.m.read_json(self.evidence)
        self.assertNotEqual(recorded["rules"]["prompt_build"]["sha256"], self.m._rules(self.root)["prompt_build"]["sha256"])
        again = self.m.prepare(self.root, "eq-run")
        self.assertEqual(again, recorded, "recorded provenance must stay untouched")
        self.assertEqual(self.m.read_json(self.evidence), recorded)

    def test_pack_comment_edit_keeps_the_run_valid_but_pack_hash_is_still_required(self):
        path = self.root / PACKS / "american-street.pack.yaml"
        path.write_text("# comment-only edit\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
        self.m.prepare(self.root, "eq-run")
        broken = self.m.read_json(self.evidence)
        broken["previews"][0]["pack"]["sha256"] = "not-a-hash"
        self.m.write_json(self.evidence, broken)
        with self.assertRaisesRegex(ValueError, "stale pack"):
            self.m.prepare(self.root, "eq-run")

    def test_prompt_affecting_edit_invalidates_only_that_style_by_name(self):
        path = self.root / PACKS / "ecommerce-studio.pack.yaml"
        text = path.read_text(encoding="utf-8")
        self.assertIn("lighting_palette:", text)
        path.write_text(text.replace("neutral white balance", "warm white balance"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, r"ecommerce-studio: prompt is not reproducible"):
            self.m.prepare(self.root, "eq-run")

    def test_rules_record_must_keep_the_expected_shape(self):
        broken = self.m.read_json(self.evidence)
        broken["rules"]["prompt_build"]["path"] = "somewhere/else.md"
        self.m.write_json(self.evidence, broken)
        with self.assertRaisesRegex(ValueError, "stale or invalid rules"):
            self.m.prepare(self.root, "eq-run")


if __name__ == "__main__":
    unittest.main()
