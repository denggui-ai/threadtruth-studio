"""Pilot gates: the ecommerce-studio lighting/expression candidate must enter the real preview input and stay scoped.

These checks prove that the candidate method is read by the actual action-0 consumer (tools/style_preview.py)
and that the 23 non-pilot packs keep the canonical head/gaze text byte for byte. They do not prove visual
improvement; that still requires authorized native generation and human review.
"""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "skills/threadtruth-studio/references/styles/ecommerce-studio.pack.yaml"
PROMPT_BUILD = ROOT / "skills/threadtruth-studio/references/prompt-build.md"
PILOT = "ecommerce-studio"
BASELINE_MOOD_CUES = ("冷静疏离", "营业", "甜美", "目录照")


def module():
    spec = importlib.util.spec_from_file_location("style_preview", ROOT / "tools/style_preview.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class EcommerceStudioLightingPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("docs/demo", "skills/threadtruth-studio/references"):
            shutil.copytree(ROOT / name, self.root / name)
        shutil.rmtree(self.root / "docs/demo/style-previews", ignore_errors=True)
        self.m = module()

    def test_pilot_scope_is_exactly_ecommerce_studio_and_geometry_has_no_mood_cues(self):
        slugs, geometry = self.m._pilot_expression_override(PROMPT_BUILD.read_text(encoding="utf-8"))
        self.assertEqual(slugs, {PILOT})
        self.assertEqual(set(geometry), set(range(1, 7)))
        for text in geometry.values():
            for cue in BASELINE_MOOD_CUES:
                self.assertNotIn(cue, text)
        canonical, _ = self.m._canonical_action_zero(self.root)
        self.assertEqual(len(canonical), 6)
        self.assertIn("冷静疏离", canonical[1]["head_gaze"], "canonical §2 table must stay untouched")

    def test_lighting_method_is_written_as_visible_relations(self):
        visual = self.m._visual(PACK.read_text(encoding="utf-8"))
        lighting = visual["lighting"].lower()
        for phrase in ("key light", "camera-left", "fill", "contact shadow", "backdrop", "same light direction"):
            self.assertIn(phrase, lighting)
        self.assertNotIn("even soft-box", lighting)
        self.assertNotIn("low shadow", lighting)
        self.assertNotIn("even soft lighting", visual["mood"])
        self.assertIn("fabric texture", visual["mood"])
        self.assertIn("relaxed", visual["persona"])
        # 2026-09-16 slimming: lighting never names garment parts, persona never implies pockets or a direct gaze,
        # and the lighting block stays short enough to survive inside a six-cell preview prompt.
        for part in ("lapel", "pocket", "sleeve", "flap"):
            self.assertNotIn(part, lighting)
        self.assertNotIn("pocket", visual["persona"])
        self.assertNotIn("direct", visual["persona"])
        self.assertIn("when standing", visual["persona"])
        self.assertLessEqual(len(visual["lighting"].split()), 80)

    def test_pilot_prompt_carries_anchor_ignore_framing_and_photoreal_lines(self):
        run = self.m.prepare(self.root, "pilot-run-2", "beige-blazer-denim-outfit")
        directory = self.m.run_dir(self.root, "pilot-run-2")
        prompts = {
            preview["style"]: (directory / "prompts" / f"{preview['style']}.txt").read_text(encoding="utf-8")
            for preview in run["previews"]
        }
        pilot = prompts[PILOT]
        self.assertIn(self.m.PILOT_ANCHOR_IGNORE, pilot)
        self.assertIn(self.m.PILOT_PHOTOREAL_LINE, pilot)
        self.assertEqual(pilot.count("Framing: " + self.m.PILOT_FRAMING["full-body"]), 4)
        self.assertEqual(pilot.count("Framing: half-body-permitted"), 2)
        for style, prompt in prompts.items():
            if style == PILOT:
                continue
            self.assertNotIn(self.m.PILOT_ANCHOR_IGNORE, prompt, style)
            self.assertNotIn(self.m.PILOT_PHOTOREAL_LINE, prompt, style)
            self.assertEqual(prompt.count("Framing: full-body"), 4, style)

    def test_single_prompt_is_one_final_stage_image_for_one_pose(self):
        result = self.m.single_prompt(self.root, "pilot-single", PILOT, 1, "beige-blazer-denim-outfit", "1:1")
        text = (self.root / result["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["sha256"], self.m.digest(text.encode()))
        self.assertEqual(text.count("POSE "), 1)
        self.assertIn("POSE 1: SIDE_TURN_STANDING", text)
        self.assertIn("exact 1:1 square canvas", text)
        general, full_body = self.m._final_negatives(self.root)
        self.assertIn("no collage, no grid", general)
        self.assertIn(general, text)
        self.assertIn(full_body, text)
        self.assertNotIn("contact-sheet", text)
        self.assertNotIn("Preview negative", text)
        self.assertIn(self.m.PILOT_ANCHOR_IGNORE, text)
        self.assertIn("Framing: " + self.m.PILOT_FRAMING["full-body"], text)
        self.assertFalse((self.m.run_dir(self.root, "pilot-single") / "evidence.json").exists())
        half = self.m.single_prompt(self.root, "pilot-single", PILOT, 3, "beige-blazer-denim-outfit", "4:5")
        half_text = (self.root / half["path"]).read_text(encoding="utf-8")
        self.assertIn("exact 4:5 portrait canvas", half_text)
        self.assertNotIn(full_body, half_text)
        with self.assertRaises(ValueError):
            self.m.single_prompt(self.root, "pilot-single", PILOT, 7, "beige-blazer-denim-outfit")
        with self.assertRaises(ValueError):
            self.m.single_prompt(self.root, "pilot-single", PILOT, 1, "beige-blazer-denim-outfit", "square")

    def test_pilot_method_enters_real_preview_prompt_and_other_packs_stay_unchanged(self):
        run = self.m.prepare(self.root, "pilot-run", "beige-blazer-denim-outfit")
        directory = self.m.run_dir(self.root, "pilot-run")
        prompts = {
            preview["style"]: (directory / "prompts" / f"{preview['style']}.txt").read_text(encoding="utf-8")
            for preview in run["previews"]
        }
        canonical, _ = self.m._canonical_action_zero(self.root)
        pilot = prompts[PILOT]
        self.assertIn("contact shadow", pilot)
        self.assertIn("no flat shadowless lighting", pilot)
        self.assertIn(self.m.PILOT_EXPRESSION_NOTE, pilot)
        for cue in BASELINE_MOOD_CUES:
            self.assertNotIn(cue, pilot)
        preview = next(item for item in run["previews"] if item["style"] == PILOT)
        self.assertEqual([pose["master"] for pose in preview["poses"]], [pose["master"] for pose in canonical])
        self.assertEqual(preview["mode"], "B")
        for style, prompt in prompts.items():
            if style == PILOT:
                continue
            for pose in canonical:
                self.assertIn(pose["head_gaze"], prompt, style)
            self.assertNotIn(self.m.PILOT_EXPRESSION_NOTE, prompt, style)


if __name__ == "__main__":
    unittest.main()
