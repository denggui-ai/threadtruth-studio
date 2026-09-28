import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('web_task', ROOT/'skills/threadtruth-studio/scripts/web-task.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class WebTaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.ref=self.root/'source.png';Image.new('RGB',(20,30),'red').save(self.ref)
        self.job=self.root/'job'
        m.create(self.job,[self.ref],['pose '+str(i) for i in range(6)],(20,30),True)
    def tearDown(self):self.tmp.cleanup()
    def authorize(self):m.update(self.job,'authorize',note='User approved this outfit six images to ChatGPT',limit=6)
    def reserve(self):return m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),conversation='https://chatgpt.com/c/test')
    def result(self,color='blue'):
        p=self.root/(color+'.png');Image.new('RGB',(20,30),color).save(p);return p
    def test_requires_authorization_and_upload_readiness(self):
        with self.assertRaises(ValueError):self.reserve()
        self.authorize()
        with self.assertRaises(ValueError):m.update(self.job,'reserve',look=1,refs=m.reference_hashes(self.job,1),ready=False,conversation='https://chatgpt.com/c/test')
        self.assertEqual(m.read(self.job)['attempts'],0)
    def test_reservation_blocks_duplicate_and_resume_does_not_reset(self):
        self.authorize();self.reserve()
        with self.assertRaises(ValueError):self.reserve()
        m.update(self.job,'mode',mode='manual')
        self.assertEqual(m.read(self.job)['attempts'],1)
        m.update(self.job,'unknown',look=1)
        with self.assertRaises(ValueError):self.reserve()
    def test_anchor_and_sequential_gate(self):
        self.authorize()
        with self.assertRaises(ValueError):m.update(self.job,'reserve',look=2,ready=True,refs=[],conversation='https://chatgpt.com/c/test')
        self.reserve();m.update(self.job,'returned',look=1,file=self.result())
        with self.assertRaises(ValueError):m.reference_hashes(self.job,2)
        m.update(self.job,'accept',look=1,note='Reviewed garment, anatomy and identity',qa='qa-pass')
        self.assertEqual(len(m.reference_hashes(self.job,2)),2)
        with self.assertRaises(ValueError):m.update(self.job,'reserve',look=2,ready=True,refs=list(reversed(m.reference_hashes(self.job,2))),conversation='https://chatgpt.com/c/test2')
    def test_wrong_size_and_duplicate_results_block(self):
        self.authorize();self.reserve();bad=self.root/'bad.png';Image.new('RGB',(30,20)).save(bad)
        with self.assertRaises(ValueError):m.update(self.job,'returned',look=1,file=bad)
        self.assertEqual(m.read(self.job)['looks'][0]['state'],'reserved')
        image=self.result();m.update(self.job,'returned',look=1,file=image);m.update(self.job,'accept',look=1,note='visual QA',qa='qa-pass')
        m.update(self.job,'reserve',look=2,ready=True,refs=m.reference_hashes(self.job,2),conversation='https://chatgpt.com/c/test2')
        with self.assertRaises(ValueError):m.update(self.job,'returned',look=2,file=image)
    def test_changed_frozen_reference_blocks(self):
        self.authorize();(self.job/'references/01.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.reserve()
    def test_no_premature_complete_or_auto_ready(self):
        self.assertFalse(m.read(self.job)['complete'])
        with self.assertRaises(ValueError):m.update(self.job,'accept',look=1,note='QA',qa='qa-pass')
    def test_handoff_locks_later_images_and_preserves_mode_budget(self):
        m.export(self.job);self.assertTrue((self.job/'handoff/look-1/prompt.txt').exists())
        self.assertFalse((self.job/'handoff/look-2/prompt.txt').exists())
        self.assertIn('look-2',(self.job/'handoff/README.md').read_text())
    def test_authorization_cannot_reset_used_budget(self):
        self.authorize();self.reserve()
        with self.assertRaises(ValueError):self.authorize()

    def test_new_chat_reserves_before_url_exists_and_binds_without_new_budget(self):
        self.authorize()
        m.update(self.job,'reserve',look=1,ready=True,refs=m.reference_hashes(self.job,1),conversation='https://chatgpt.com/',tab='dedicated-tab-1')
        m.update(self.job,'bind',look=1,conversation='https://chatgpt.com/c/new')
        self.assertEqual(m.read(self.job)['attempts'],1)
    def test_truncated_png_remains_recoverable(self):
        self.authorize();self.reserve();p=self.result();p.write_bytes(p.read_bytes()[:24])
        with self.assertRaises(ValueError):m.update(self.job,'returned',look=1,file=p)
        self.assertEqual(m.read(self.job)['looks'][0]['state'],'reserved')
    def test_deleted_non_anchor_stops_progression(self):
        self.authorize();self.reserve()
        for n,color in [(1,'blue'),(2,'green')]:
            if n==2:m.update(self.job,'reserve',look=n,ready=True,refs=m.reference_hashes(self.job,n),conversation='https://chatgpt.com/c/test2')
            m.update(self.job,'returned',look=n,file=self.result(color));m.update(self.job,'accept',look=n,note='Visual QA',qa='qa-pass')
        (self.job/'outputs/look-2.png').unlink()
        with self.assertRaises((ValueError,OSError)):m.update(self.job,'reserve',look=3,ready=True,refs=m.reference_hashes(self.job,3),conversation='https://chatgpt.com/c/test3')
    def test_save_syncs_file_and_directory(self):
        from unittest.mock import patch
        with patch.object(m.os,'fsync') as sync:m.save(self.job,m.read(self.job))
        self.assertEqual(sync.call_count,2)
