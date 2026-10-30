"""The runtime quickstart must stay executable: drive the documented CLI chain with synthetic images, zero generation."""
import hashlib, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/threadtruth-studio'
SCRIPTS = SKILL / 'scripts'
QUICKSTART = SKILL / 'references/runtime-quickstart.md'
SIZE = [2, 3]   # ratio-first: the first returned image fixes the pixel baseline
PIX = (40, 60)
MODEL = dict(source_type='new', scope='full', subject='adult female model', locked=[], adjustable=[], consent_note='')


class RuntimeQuickstartTests(unittest.TestCase):
    def test_skill_gate_points_at_quickstart_and_every_named_script_exists(self):
        skill = (SKILL / 'SKILL.md').read_text()
        self.assertIn('不经账本脚本，绝不生图', skill)
        self.assertIn('references/runtime-quickstart.md', skill)
        text = QUICKSTART.read_text()
        for name in set(re.findall(r'scripts/([\w-]+\.py)', text)):
            self.assertTrue((SCRIPTS / name).is_file(), name)
        order = ['prepare', 'init', 'authorize', 'export', 'reserve', 'returned', 'accept', 'finish-preview', 'prepare-delivery', 'confirm-model']
        positions = [text.find('web-task.py" ' + cmd) if cmd != 'prepare' else text.find('visual_library.py" prepare') for cmd in order]
        self.assertTrue(all(p >= 0 for p in positions), positions)
        self.assertEqual(positions, sorted(positions), 'quickstart commands must appear in execution order')
        self.assertNotIn('/Users/', text)
        self.assertIn('ratio-first', text)

    def cli(self, script, *args, cwd):
        result = subprocess.run([sys.executable, str(SCRIPTS / script)] + [str(a) for a in args], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout) if result.stdout.strip().startswith('{') else result.stdout

    def synth(self, root, name, color):
        path = root / name; Image.new('RGB', PIX, color).save(path); return path

    def handoff(self, task, look):
        folder = sorted((task / 'handoff').glob(f'look-{look}-v*'))[-1]
        return json.loads((folder / 'manifest.json').read_text()), (folder / 'prompt.txt').read_text(), json.loads((folder / 'request.json').read_text()), folder

    def test_quickstart_chain_runs_offline_with_synthetic_images(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root = Path(temp.name)
        src = self.synth(root, 'product.png', 'red'); h = hashlib.sha256(src.read_bytes()).hexdigest()
        looks = [dict(slot=i, shot_id='qs-' + str(i), display_goal='Show the set', must_show=['hem'], reason='Front flat-lay supports it.',
                      body_action='Stand naturally, action ' + str(i), hands='Hands relaxed', support='Both feet grounded', framing='full-body',
                      garment_views=['front'], reference_sha256s=[h], head='natural', gaze='soft') for i in range(1, 10)]
        shot_plan = dict(version=2, sku='qs-sku', route='B', coverage=[dict(sha256=h, views=['front'], usable=True, same_sku=True, note='Synthetic front')],
                         looks=looks, selected_shot_ids=[l['shot_id'] for l in looks], series_role='series')   # no framing_guidance: init must default it
        prep = dict(entry_id='french-effortless', garment=dict(description='Synthetic red garment.', keep=['red'], source_sha256s=[h]),
                    inventory=[dict(role='garment-source', sha256=h)], model=MODEL, output_form='human', shot_plan=shot_plan)
        (root / 'prepare.json').write_text(json.dumps(prep))
        self.cli('visual_library.py', 'prepare', '--spec', root / 'prepare.json', '--output', root / 'visual_plan.json', cwd=root)
        visual = json.loads((root / 'visual_plan.json').read_text()); self.assertEqual(len(visual['shots']), 9)
        ctx = dict(outfit='qs-sku', style='french-effortless', mode='C', output_form='human', size=SIZE, first_pose=1, canvas_policy='ratio-first')
        (root / 'init-preview.json').write_text(json.dumps(dict(references=[dict(path=str(src), role='garment-source')], size=SIZE, route='codex_native',
                                                                model=MODEL, context=dict(ctx, purpose='preview-grid'), shot_plan=shot_plan, visual_plan=visual)))
        preview = root / 'preview'
        self.assertEqual(len(self.cli('web-task.py', 'init', '--task', preview, '--spec', root / 'init-preview.json', cwd=root)['looks']), 1)
        self.cli('web-task.py', 'authorize', '--task', preview, '--limit', 1, '--note', 'one preview', cwd=root)
        self.cli('web-task.py', 'export', '--task', preview, cwd=root)
        man, prompt, request, folder = self.handoff(preview, 1)
        self.assertIn('PREVIEW ONLY', prompt); self.assertIn('head-height', prompt); self.assertEqual(request['prompt'], prompt)
        self.assertEqual([Path(p).name for p in request['referenced_image_paths']], ['01-garment-source.png'])
        self.cli('web-task.py', 'reserve', '--task', preview, '--look', 1, '--ready', '--refs', *man['reference_hashes'], '--expected-plan-sha256', man['current_plan_sha256'], cwd=root)
        self.cli('web-task.py', 'returned', '--task', preview, '--look', 1, '--file', self.synth(root, 'preview.png', 'blue'), cwd=root)
        self.cli('web-task.py', 'accept', '--task', preview, '--look', 1, '--qa', 'qa-pass', '--note', 'grid readable', cwd=root)
        self.cli('web-task.py', 'finish-preview', '--task', preview, '--decision', 'direction-confirmed', '--note', 'direction ok', cwd=root)
        delivery = root / 'delivery'
        (root / 'delivery.json').write_text(json.dumps(dict(context=dict(ctx, purpose='delivery'), size=SIZE, count=9, series_role='series')))
        d = self.cli('web-task.py', 'prepare-delivery', '--task', delivery, '--preview-task', preview, '--spec', root / 'delivery.json', '--note', 'nine please', cwd=root)
        self.assertEqual(len(d['looks']), 9); self.assertEqual(d['total_attempts'], 1)
        self.cli('web-task.py', 'authorize', '--task', delivery, '--limit', 2, '--note', 'two for now', cwd=root)
        for look, color in ((1, 'green'), (2, 'yellow')):
            self.cli('web-task.py', 'export', '--task', delivery, cwd=root)
            man, prompt, request, folder = self.handoff(delivery, look)
            self.assertIn('head-height', prompt); self.assertIn(f'Shot {look}: qs-{look}.', prompt)
            self.cli('web-task.py', 'reserve', '--task', delivery, '--look', look, '--ready', '--refs', *man['reference_hashes'], '--expected-plan-sha256', man['current_plan_sha256'], cwd=root)
            self.cli('web-task.py', 'returned', '--task', delivery, '--look', look, '--file', self.synth(root, f'look-{look}.png', color), cwd=root)
            self.cli('web-task.py', 'accept', '--task', delivery, '--look', look, '--qa', 'qa-user-review', '--note', 'fine details for user', cwd=root)
            if look == 1:
                self.cli('web-task.py', 'confirm-model', '--task', delivery, '--look', 1, '--note', 'person ok', cwd=root)
        self.assertEqual([Path(p).name for p in request['referenced_image_paths']], ['01-garment-source.png', '02-identity-only.png'])
        status = self.cli('web-task.py', 'status', '--task', delivery, cwd=root)
        self.assertEqual(status['attempts'], 2); self.assertTrue(status['model_confirmation'])
        self.assertEqual(status['shot_plan']['framing_guidance'], 1)
        self.assertEqual(json.loads((preview / 'task.json').read_text())['shot_plan']['framing_guidance'], 1)
        self.assertEqual([l['state'] for l in status['looks']][:3], ['accepted', 'accepted', 'pending'])


if __name__ == '__main__': unittest.main()
