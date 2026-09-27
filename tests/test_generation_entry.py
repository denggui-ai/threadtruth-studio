import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'skills/threadtruth-studio'
SCRIPT = RUNTIME / 'scripts/recommend-entry.py'
spec = importlib.util.spec_from_file_location('generation_entry', SCRIPT)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class GenerationEntryTests(unittest.TestCase):
    def test_selection_cases(self):
        cases = json.loads((ROOT / 'evals/generation-entry-evals.json').read_text())
        for case in cases:
            with self.subTest(case=case['id']):
                result = entry.recommend(**case['input'])
                for key, value in case['expected'].items():
                    self.assertEqual(result[key], value)
                self.assertFalse(result['generation_authorized'])
                self.assertFalse(result['model_attribution_allowed'])

    def test_all_registered_styles_keep_default_but_allow_manual_override(self):
        data = entry.load_evidence()
        packs = {p.name.removesuffix('.pack.yaml') for p in (RUNTIME/'references/styles').glob('*.pack.yaml') if not p.name.startswith('_')}
        self.assertEqual(set(data['rendering_results']), packs)
        for style, outcome in data['rendering_results'].items():
            with self.subTest(style=style):
                expected = outcome if outcome in entry.ROUTES else 'codex_native'
                result = entry.recommend(style=style, goal='rendering')
                self.assertEqual(result['recommended_route'], expected)
                self.assertEqual(result['selected_route'], 'codex_native')
                for chosen in entry.ROUTES:
                    self.assertEqual(entry.recommend(style=style, goal='rendering', selected=chosen)['selected_route'], chosen)

    def test_evidence_counts_do_not_treat_missing_as_tie(self):
        from collections import Counter
        self.assertEqual(Counter(entry.load_evidence()['rendering_results'].values()),
                         {'chatgpt_web':11,'codex_native':7,'tie':1,'missing_pair':5})

    def test_invalid_route_and_goal_fail_instead_of_silently_falling_back(self):
        for kwargs in ({'selected':'api'}, {'goal':'speed'}):
            with self.assertRaises(ValueError):
                entry.recommend(**kwargs)

    def test_cli_works_outside_repo_and_does_not_generate(self):
        run = subprocess.run([sys.executable,str(SCRIPT),'--style','italian-luxe','--goal','rendering','--selected','codex_native'],cwd='/tmp',text=True,capture_output=True,check=True)
        result = json.loads(run.stdout)
        self.assertEqual(result['recommended_route'],'chatgpt_web')
        self.assertEqual(result['selected_route'],'codex_native')
        self.assertFalse(result['generation_authorized'])
