"""WP-21 orchestration: identity-only lock, per-shot variety, commitments, asset trace."""
import importlib.util
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/threadtruth-studio/scripts'


def module(name):
    spec = importlib.util.spec_from_file_location('wp21_' + name, SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


model_reference = module('model_reference')


class IdentityLockTests(unittest.TestCase):
    def model(self, **changes):
        result = dict(source_type='ai', scope='full', subject='adult female model',
                      locked=['apparent age around 40'], adjustable=['gentle makeup'], consent_note='')
        result.update(changes)
        return result

    def test_styling_lock_default_is_identity_only_and_full_retains_hair_makeup(self):
        default = '\n'.join(model_reference.prompt_lines(self.model()))
        self.assertNotIn('Retain reference hair and makeup', default)
        self.assertIn('hair, makeup and expression follow the selected style plan', default)
        self.assertIn('body proportions', default)
        full = '\n'.join(model_reference.prompt_lines(self.model(styling_lock='full')))
        self.assertIn('Retain reference hair and makeup', full)
        face_only = '\n'.join(model_reference.prompt_lines(self.model(scope='face')))
        self.assertNotIn('body proportions', face_only.split('hair, makeup')[0].split('Identity references')[-1])
        with self.assertRaises(ValueError):
            model_reference.validate_model(self.model(styling_lock='half'))

    def test_identity_lock_lets_style_hair_makeup_through_but_full_filters_them(self):
        persona = 'cool detached poise; soft matte makeup; loose hair'
        plain = self.model(adjustable=[])
        self.assertIn('makeup', model_reference.resolve_persona(plain, persona))
        self.assertIn('loose hair', model_reference.resolve_persona(plain, persona))
        full = model_reference.resolve_persona(dict(plain, styling_lock='full'), persona)
        self.assertNotIn('makeup', full)
        self.assertNotIn('loose hair', full)
