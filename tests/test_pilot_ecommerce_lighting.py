"""Shared head/gaze assembly and scoped ecommerce photography checks.

These exercise action-0 and action-2 prompts, not image quality. Visual improvement
still requires authorized native generation and human review.
"""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "skills/threadtruth-studio/references/styles/ecommerce-studio.pack.yaml"
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

    def test_head_rule_edits_reach_preview_and_single_without_changing_photography(self):
        before = self.m.prepare(self.root, "before-head-edit", "beige-blazer-denim-outfit")
        rule = self.root / "skills/threadtruth-studio/references/prompt-build.md"
        rule.write_text(rule.read_text(encoding="utf-8").replace(
            "头颈放松,符合倚靠关系", "头颈随墙面支撑自然放松"
        ), encoding="utf-8")
        after = self.m.prepare(self.root, "after-head-edit", "beige-blazer-denim-outfit")
        for old, new in zip(before["previews"], after["previews"]):
            with self.subTest(style=new["style"]):
                self.assertNotEqual(old["prompt_sha256"], new["prompt_sha256"])
                for field in ("visual", "pack", "layout_contract", "negative_delta_add"):
                    self.assertEqual(old[field], new[field])
                self.assertEqual([p["scene"] for p in old["poses"]], [p["scene"] for p in new["poses"]])
                preview = (self.m.run_dir(self.root, "after-head-edit") / "prompts" / f"{new['style']}.txt").read_text(encoding="utf-8")
                single = self.m.single_prompt(self.root, "after-head-single", new["style"], 2, "beige-blazer-denim-outfit")
                for text in (preview, (self.root / single["path"]).read_text(encoding="utf-8")):
                    self.assertIn("Head/gaze: 头颈随墙面支撑自然放松", text)
                    self.assertEqual(self.m.PILOT_PHOTOREAL_LINE in text, new["style"] == PILOT)

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

    def test_b_mode_uses_pack_scenes_with_floor_wall_and_support(self):
        run = self.m.prepare(self.root, "pilot-scenes", "beige-blazer-denim-outfit")
        preview = next(item for item in run["previews"] if item["style"] == PILOT)
        scenes = [pose["scene"] for pose in preview["poses"]]
        self.assertEqual(len(set(scenes)), 6)
        self.assertTrue(any("floor" in scene and "horizon" in scene for scene in scenes))
        self.assertTrue(any("wall panel" in scene for scene in scenes))
        self.assertTrue(any("studio block" in scene for scene in scenes))
        prompt = (
            self.m.run_dir(self.root, "pilot-scenes") / "prompts" / f"{PILOT}.txt"
        ).read_text(encoding="utf-8")
        self.assertNotIn("Mode/scene: low-distraction white or light-gray studio background", prompt)

    def test_all_styles_share_head_relations_in_preview_and_each_single_pose(self):
        run = self.m.prepare(self.root, "shared-head", "beige-blazer-denim-outfit")
        self.assertEqual(len(run["previews"]), 24)
        masters = ["SIDE_TURN_STANDING", "SIDE_LEANING_WALL", "UPRIGHT_SEATED",
                   "FRONT_LIGHT_STEP", "SLIGHT_FORWARD_LEAN", "BACK_TURN_GLANCE"]
        banned = ("冷静疏离", "不正面营业", "避免甜美手托腮", "避免目录照", "头部微垂", "视线垂落", "画面右侧", "画面左侧",
                  "视线避开镜头", "视线不直对镜头", "no cold or detached editorial mood")
        for preview in run["previews"]:
            with self.subTest(style=preview["style"]):
                self.assertEqual([p["master"] for p in preview["poses"]], masters)
                grid = (self.m.run_dir(self.root, "shared-head") / "prompts" / f"{preview['style']}.txt").read_text(encoding="utf-8")
                self.assertEqual(grid.count("Head/gaze: "), 6)
                self.assertEqual(preview["prompt_sha256"], self.m.digest(grid.encode()))
                self.assertIn("Head/gaze: 保留越肩回看,避免过度扭颈", grid)
                for pose in preview["poses"]:
                    single = self.m.single_prompt(self.root, "shared-head-single", preview["style"], pose["ordinal"], "beige-blazer-denim-outfit")
                    text = (self.root / single["path"]).read_text(encoding="utf-8")
                    self.assertEqual(text.count("Head/gaze: "), 1)
                    self.assertIn(f"Head/gaze: {pose['head_gaze']}", text)
                    for output in (grid, text):
                        self.assertEqual(output.count("Head/gaze guidance:"), 1)
                        self.assertIn(f"Attitude: {preview['visual']['persona']}", output)
                        for cue in banned:
                            self.assertNotIn(cue, output)

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

    def test_style_personas_remain_distinct_with_shared_head_rules(self):
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
        for cue in BASELINE_MOOD_CUES:
            self.assertNotIn(cue, pilot)
        preview = next(item for item in run["previews"] if item["style"] == PILOT)
        self.assertEqual([pose["master"] for pose in preview["poses"]], [pose["master"] for pose in canonical])
        self.assertEqual(preview["mode"], "B")
        for style, prompt in prompts.items():
            for pose in canonical:
                self.assertIn(pose["head_gaze"], prompt, style)
        self.assertIn("Attitude: calm, detached, quietly confident", prompts["korean-cold-editorial"])
        self.assertIn("Attitude: gentle natural ease", prompts["japanese-lifestyle"])
        self.assertIn("Attitude: energetic relaxed expression", prompts["athleisure"])
        self.assertIn("Attitude: neutral approachable expression", pilot)


if __name__ == "__main__":
    unittest.main()
