"""Local pose catalog metadata and execution-source boundaries; no network."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/threadtruth-studio/scripts/pose_catalog.py'


class PoseCatalogTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('pose_catalog_test', SCRIPT)
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_source_declaration_and_known_research_source_cannot_be_relabelled(self):
        row = dict(role='pose-reference', sha256='a' * 64, pose_source=dict(
            source_id='studio-owned', group_id='stand-1', view='front', usage='owned', note='Original owned photograph.'))
        self.catalog.validate_reference(row)
        row['pose_source']['source_id'] = 'anhao/ai-pose-gallery-zh'
        with self.assertRaisesRegex(ValueError, 'research'):
            self.catalog.validate_reference(row)
        row['role'] = 'aesthetic-reference'
        with self.assertRaisesRegex(ValueError, 'research'):
            self.catalog.check_inventory([row])

    def test_known_repository_path_blocked_in_every_role(self):
        for role in ('garment-source', 'identity-reference', 'aesthetic-reference', 'pose-reference'):
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'research'):
                self.catalog.check_inventory([dict(role=role, path='/tmp/ai-pose-gallery-zh/img/full_single_P015_front.png')])

    def test_symlink_cannot_hide_known_research_source_path(self):
        target = self.root / 'ai-pose-gallery-zh' / 'img' / 'source.png'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'synthetic research fixture')
        link = self.root / 'renamed.png'
        link.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'research'):
            self.catalog.check_source(dict(path=link, role='aesthetic-reference'))

    def test_original_gallery_adapter_is_readonly_research_and_groups_namespace(self):
        raw = [dict(id='full_single_P001_front', 姿势名称='自然站姿', 分类='站姿', 原图='img/a.png'),
               dict(id='upper80v2_P001_front', 姿势名称='低位手势', 分类='可爱', 原图='img/b.png')]
        path = self.root / 'pose-zh.json'
        path.write_text(json.dumps(raw, ensure_ascii=False))
        loaded = self.catalog.load(path)
        self.assertEqual(len(loaded['entries']), 2)
        self.assertEqual(loaded['usage'], 'research-only')
        self.assertEqual({x['group_id'] for x in loaded['entries']}, {'full_single_P001', 'upper80v2_P001'})
        self.assertEqual(len(self.catalog.search(loaded, query='站姿')), 1)
        self.assertEqual(len(self.catalog.search(loaded, source_id='anhao/ai-pose-gallery-zh', view='front')), 2)
        with self.assertRaisesRegex(ValueError, 'research'):
            self.catalog.reference(loaded, 'full_single_P001', 'front')

    def test_owned_catalog_exports_reviewed_reference_with_verified_hash(self):
        image = self.root / 'pose.png'
        image.write_bytes(b'synthetic bytes; image validation belongs to the execution inventory')
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        doc = dict(version=1, source_id='studio', usage='owned', note='Owned studio material.', entries=[
            dict(group_id='stand', view='front', path='pose.png', sha256=digest, title='Relaxed standing',
                 body_action='Stand upright.', hands='Low arms.', support='Two feet.',
                 occludes=[], suitable_for=['printed top'], review_note='Actual view reviewed.')])
        path = self.root / 'owned.json'
        path.write_text(json.dumps(doc))
        loaded = self.catalog.load(path)
        ref = self.catalog.reference(loaded, 'stand', 'front')
        self.assertEqual(ref['sha256'], digest)
        self.assertEqual(ref['pose_source']['usage'], 'owned')
        self.assertEqual(ref['path'], str(image.resolve()))
        image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.catalog.reference(loaded, 'stand', 'front')

    def test_no_execution_without_view_review_or_source_note(self):
        row = dict(role='pose-reference', sha256='a' * 64, pose_source=dict(
            source_id='studio', group_id='stand', view='front', usage='authorized', note=''))
        with self.assertRaises(ValueError):
            self.catalog.validate_reference(row)

    def test_pre_copy_source_check_does_not_read_or_require_image_hash(self):
        row = dict(path='/not-created/owned.png', role='pose-reference', pose_source=dict(
            source_id='studio', group_id='stand', view='front', usage='owned', note='Owned and reviewed.'))
        self.catalog.check_source(row)
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.catalog.check_inventory([row])

    def test_cli_help(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('source', result.stdout)


if __name__ == '__main__':
    unittest.main()
