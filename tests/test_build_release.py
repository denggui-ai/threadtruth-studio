import importlib.util
import json
import re
import shutil
import tempfile
import unittest
import zipfile
from urllib.parse import unquote, urlsplit
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build-release.py"


class ReleaseBuildTests(unittest.TestCase):
    def test_allowlist_release_excludes_development_material(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as output_dir:
            archive, checksum = module.build_release(ROOT, Path(output_dir))
            self.assertTrue(archive.is_file())
            self.assertTrue(checksum.is_file())
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())

            version = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())["version"]
            prefix = f"lookset-{version}/"
            self.assertIn(prefix + ".codex-plugin/plugin.json", names)
            self.assertIn(prefix + "skills/lookset/SKILL.md", names)
            self.assertIn(prefix + "skills/lookset/scripts/pose_catalog.py", names)
            self.assertIn(prefix + "skills/lookset/references/pose-planning.md", names)
            self.assertFalse(any("ai-pose-gallery" in name or name.endswith("pose-zh.json")
                                 or re.search(r"(?:full_single|full_sexy|upper80v2|pair60)_P\d+.*\.(?:png|jpg)$", name)
                                 for name in names), "Research gallery images/data must not ship")
            self.assertIn(prefix + "USER-GUIDE.html", names)
            self.assertIn(prefix + "install-local.py", names)
            self.assertIn(prefix + "CONTRIBUTING.md", names)
            self.assertIn(prefix + "SECURITY.md", names)
            self.assertNotIn(prefix + "docs/BETA9-TRYOUT.md", names)
            self.assertNotIn(prefix + "docs/BETA10-TRYOUT.md", names)
            self.assertNotIn(prefix + "docs/BETA11-TRYOUT.md", names)
            self.assertNotIn(prefix + "docs/BETA12-TRYOUT.md", names)
            self.assertNotIn(prefix + "docs/MODEL-REUSE-CANDIDATE.md", names)
            self.assertNotIn(prefix + "docs/BETA-ACCEPTANCE.md", names)
            self.assertNotIn(prefix + "docs/COMPETITIVE-LANDSCAPE.md", names)
            self.assertFalse(any("/docs/demo/" in name for name in names))
            self.assertEqual(len([name for name in names
                                  if "/pose-library/images/" in name]), 60)
            self.assertLessEqual(archive.stat().st_size, 20_000_000)
            for excluded in ("CHANGELOG.md", "RELEASE.md", "ROADMAP.md", "docs/WORK-STATUS.md", "docs/CODEX-FOR-OSS.md", "docs/demo/GROWTH.md"):
                self.assertNotIn(prefix + excluded, names)
            self.assertFalse(any("/docs/verification/" in name for name in names))
            self.assertFalse(any("/docs/superpowers/" in name for name in names))
            self.assertFalse(any("/evals/" in name for name in names))
            self.assertFalse(any("/tests/" in name for name in names))
            self.assertFalse(any("/tools/" in name for name in names))
            self.assertFalse(any("/.threadtruth/" in name for name in names))
            self.assertFalse(any(name.endswith("image-1.png") for name in names))

    def test_public_repo_extras_match_readme_demo_files(self):
        extras = (ROOT / "tools/public-repo-extra.txt").read_text().splitlines()
        referenced = set()
        for name in ("README.md", "README.zh-CN.md"):
            for target in re.findall(r"docs/demo/[^\s)\"'<>]+", (ROOT / name).read_text()):
                path = ROOT / target
                if path.is_file():
                    referenced.add(target)
        self.assertEqual(extras, sorted(referenced))
        self.assertTrue(all((ROOT / name).is_file() for name in extras))

    def test_release_document_local_links_are_shipped(self):
        spec = importlib.util.spec_from_file_location("build_release_links", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as output_dir:
            archive, _ = module.build_release(ROOT, Path(output_dir))
            stage = Path(output_dir) / archive.stem
            missing = []
            for document in stage.rglob("*"):
                if document.suffix not in (".md", ".html"):
                    continue
                content = document.read_text()
                links = re.findall(r"\]\(([^\s)]+)", content)
                links += re.findall(r"(?:href|src)=[\"']([^\"']+)", content)
                for link in links:
                    parsed = urlsplit(link)
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    if not (document.parent / unquote(parsed.path)).exists():
                        missing.append(f"{document.relative_to(stage)} -> {link}")
            self.assertEqual(missing, [], "Offline links must resolve; source-only references need an explicit online URL")

    def test_release_rejects_tampered_primary_demo_media(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp_dir:
            clone = Path(temp_dir) / "repo"
            shutil.copytree(
                ROOT,
                clone,
                ignore=shutil.ignore_patterns(".git", "dist", ".threadtruth", "__pycache__"),
            )
            target = (
                clone
                / "docs"
                / "demo"
                / "primary-cases"
                / "white-hooded-puffer-vest-korean-cold"
                / "look-4.jpg"
            )
            target.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "public demo rights validation failed"):
                module.build_release(clone, Path(temp_dir) / "out")

    def test_release_fails_when_public_demo_rights_are_invalid(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp_dir:
            clone = Path(temp_dir) / "repo"
            shutil.copytree(
                ROOT,
                clone,
                ignore=shutil.ignore_patterns(".git", "dist", ".threadtruth", "__pycache__"),
            )
            case = clone / "docs" / "demo" / "cases" / "bad-case"
            case.mkdir(parents=True)
            (case / "source.jpg").write_bytes(b"tampered")
            (case / "source-metadata.json").write_text(
                json.dumps({"objectID": 1, "isPublicDomain": False, "primaryImage": ""})
            )
            (case / "rights.json").write_text(
                json.dumps(
                    {
                        "status": "promoted",
                        "role": "auxiliary",
                        "source_license": {"id": "CC-BY-4.0"},
                        "media_license": {"id": "CC-BY-4.0"},
                        "asset": {"sha256": "wrong"},
                        "source": {"object_id": 1},
                    }
                )
            )
            (case / "README.md").write_text("invalid")
            with self.assertRaisesRegex(ValueError, "public demo rights validation failed"):
                module.build_release(clone, Path(temp_dir) / "out")

    def test_release_rejects_unregistered_demo_media(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp_dir:
            clone = Path(temp_dir) / "repo"
            shutil.copytree(
                ROOT,
                clone,
                ignore=shutil.ignore_patterns(".git", "dist", ".threadtruth", "__pycache__"),
            )
            for name in ("unregistered.jpg", "unregistered.jfif", "unregistered.mp4", "unregistered"):
                path = clone / "docs" / "demo" / name
                path.write_bytes(b"not registered")
                with self.assertRaisesRegex(ValueError, "unregistered demo"):
                    module.build_release(clone, Path(temp_dir) / "out")
                path.unlink()

    def test_release_rejects_stale_rights_index_without_cases_directory(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp_dir:
            clone = Path(temp_dir) / "repo"
            shutil.copytree(
                ROOT,
                clone,
                ignore=shutil.ignore_patterns(".git", "dist", ".threadtruth", "__pycache__"),
            )
            shutil.rmtree(clone / "docs" / "demo" / "cases", ignore_errors=True)
            (clone / "docs" / "demo" / "RIGHTS.md").write_text("stale")
            with self.assertRaisesRegex(ValueError, "rights index is stale"):
                module.build_release(clone, Path(temp_dir) / "out")

    def test_release_rejects_superseded_v1_public_preview_evidence(self):
        spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp_dir:
            clone = Path(temp_dir) / "repo"
            shutil.copytree(
                ROOT,
                clone,
                ignore=shutil.ignore_patterns(".git", "dist", ".threadtruth", "__pycache__"),
            )
            public = clone / "docs/demo/style-previews/legacy"
            public.mkdir(parents=True)
            (public / "evidence.json").write_text(
                json.dumps({"schema_version": "1.0", "run_id": "legacy", "status": "approved", "boards": []})
            )
            with self.assertRaisesRegex(ValueError, "public demo rights validation failed"):
                module.build_release(clone, Path(temp_dir) / "out")

    def _load_module(self):
        spec = importlib.util.spec_from_file_location("build_release_copy", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _synthetic_repo(self, base):
        import subprocess
        root = Path(base) / "repo"
        for name in ("skills/demo-skill", ".codex-plugin", "docs/demo"):
            (root / name).mkdir(parents=True)
        (root / "skills/demo-skill/SKILL.md").write_text("tracked")
        (root / ".codex-plugin/plugin.json").write_text("{}")
        (root / "docs/demo/README.md").write_text("tracked")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        return root

    def test_release_copy_skips_untracked_local_files(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as base:
            root = self._synthetic_repo(base)
            (root / "skills/demo-skill/private-state.json").write_text("local only")
            stage = Path(base) / "stage"
            module._copy_source_dirs(root, stage)
            self.assertTrue((stage / "skills/demo-skill/SKILL.md").is_file())
            self.assertFalse((stage / "skills/demo-skill/private-state.json").exists())

    def test_release_copy_rejects_symlinks(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as base:
            root = self._synthetic_repo(base)
            outside = Path(base) / "outside-secret.txt"
            outside.write_text("secret")
            (root / "skills/demo-skill/linked.txt").symlink_to(outside)
            import subprocess
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                module._copy_source_dirs(root, Path(base) / "stage")


    def test_release_copy_rejects_symlinked_parent_directory(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as base:
            root = self._synthetic_repo(base)
            outside = Path(base) / "outside-dir"
            shutil.move(str(root / "skills/demo-skill"), outside)
            (outside / "SKILL.md").write_text("private marker")
            (root / "skills/demo-skill").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                module._copy_source_dirs(root, Path(base) / "stage")

if __name__ == "__main__":
    unittest.main()
