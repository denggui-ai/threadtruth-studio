"""Frozen rendering digests recorded on d7d7e66, using synthetic garment data."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import unittest

from tests.test_style_pose_pool import module

ROOT = Path(__file__).resolve().parents[1]
shot, visual, task = module('shot_plan'), module('visual_plan'), module('web-task')


def legacy_cases():
    fixture = json.loads((ROOT / 'tests/fixtures/style-pool-legacy.json').read_text())
    for version, framing, variety in itertools.product((1, 2), (None, 1, 2), (None, 1, 2)):
        if version == 1 and variety is not None:
            continue
        for crop in (('full-body', 'half-body', 'knee-up', 'detail') if version == 2 else ('classic',)):
            spec, plan = copy.deepcopy(fixture['spec']), copy.deepcopy(fixture['visual_plan'])
            if version == 1:
                shots = shot.default_plan('synthetic-legacy', spec['shot_plan']['coverage'])
                plan['version'] = 1
                cell = {k: v for k, v in plan['shots'][0].items() if k not in ('slot', 'shot_id')}
                plan['shots'] = [dict(cell, slot=i, pose=i) for i in range(1, 7)]
            else:
                shots = spec['shot_plan']
                shots['looks'][0]['framing'] = crop
                if variety is None:
                    shots.pop('variety_checks', None)
                else:
                    shots['variety_checks'] = variety
            if framing is None:
                shots.pop('framing_guidance', None)
            else:
                shots['framing_guidance'] = framing
            for purpose in ('delivery', 'preview-grid'):
                context = dict(fixture['context'], purpose=purpose)
                data = dict(schema_version=2, model=spec['model'], identity=True,
                            context=context, size=[20, 30], route='codex_native',
                            shot_plan=shots, visual_plan=plan, prompt_contract_version=2,
                            references=spec['inventory'])
                if version == 2:
                    data['identity_instruction_version'] = 1
                look = None if purpose == 'preview-grid' else 1
                row = dict(number=1, prompt=visual.compile_prompt(plan, look))
                key = f'v{version}-framing{framing}-variety{variety}-{crop}-{purpose}'
                yield key, data, row


def digests():
    return {key: hashlib.sha256(task.handoff_prompt(data, row, data['references']).encode()).hexdigest()
            for key, data, row in legacy_cases()}


class AestheticLegacyTests(unittest.TestCase):
    def test_frozen_v1_v2_requests_keep_baseline_bytes(self):
        expected = json.loads((ROOT / 'tests/fixtures/aesthetic-legacy-digests.json').read_text())
        self.assertEqual(expected['baseline'], 'd7d7e66')
        self.assertEqual(digests(), expected['digests'])


if __name__ == '__main__':
    unittest.main()
