#!/usr/bin/env python3
"""Local advisory only: no generation, browser, upload, or network operations."""
import argparse
import json
from pathlib import Path

ROUTES = ('codex_native', 'chatgpt_web')
GOALS = ('balanced', 'rendering', 'fidelity', 'style', 'identity')
EVIDENCE = Path(__file__).resolve().parents[1] / 'references/generation-entry-evidence.json'


def load_evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def recommend(style=None, goal='balanced', selected=None):
    if selected is not None and selected not in ROUTES:
        raise ValueError('Choose a supported built-in entry; API fallback is not supported')
    if goal not in GOALS:
        raise ValueError('Unsupported preference goal')
    data = load_evidence()
    recommended, basis = 'codex_native', 'default'
    if goal == 'rendering':
        if style is None:
            recommended, basis = 'chatgpt_web', 'overall_sample'
        else:
            outcome = data['rendering_results'].get(style, 'unmeasured')
            if outcome in ROUTES:
                recommended, basis = outcome, 'paired_sample'
            else:
                basis = outcome  # Tie and absent evidence retain the default.
    return {
        'recommended_route': recommended,
        'selected_route': selected or 'codex_native',
        'selection_basis': 'user_choice' if selected else 'default',
        'basis': basis,
        'evidence_run': data['run_id'] if basis != 'default' else None,
        'generation_authorized': False,
        'model_attribution_allowed': False,
        'limitation': 'Single-sample entry preference, not a model ranking or fidelity guarantee.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', help='Confirmed style slug; omit for overall preference')
    parser.add_argument('--goal', choices=GOALS, default='balanced')
    parser.add_argument('--selected', choices=ROUTES, help='User-selected entry; omission keeps Codex')
    args = parser.parse_args()
    print(json.dumps(recommend(args.style, args.goal, args.selected), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
