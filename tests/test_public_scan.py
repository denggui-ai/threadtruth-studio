import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('public_scan', Path(__file__).parents[1] / 'tools/public-scan.py')
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


class PublicScanTests(unittest.TestCase):
    def test_ignored_local_evidence_excluded_but_force_tracked_or_unignored_secrets_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / '.gitignore').write_text('.threadtruth/\n.superpowers/\n')
            private = root / '.threadtruth'
            private.mkdir()
            marker = '/' + 'Users/' + 'fixture/'
            (private / 'local.json').write_text(marker)
            (root / 'README.md').write_text('public document')
            self.assertEqual(scanner.scan_tree(root), [])
            subprocess.run(['git', 'add', '-f', '.threadtruth/local.json'], cwd=root, check=True)
            self.assertEqual(len(scanner.scan_tree(root)), 1)
            (root / 'new-untracked.md').write_text(marker)
            self.assertEqual(len(scanner.scan_tree(root)), 2)

    def test_github_token_formats_are_flagged(self):
        classic = 'gh' + 'p_' + 'A1b2' * 9
        fine_grained = 'github' + '_pat_' + '11ABCDEFG0' * 3
        self.assertEqual(len(scanner.scan_text(classic, 'fixture')), 1)
        self.assertEqual(len(scanner.scan_text(fine_grained, 'fixture')), 1)
        self.assertEqual(len(scanner.scan_text('my_' + classic, 'fixture')), 1)
        self.assertEqual(scanner.scan_text('gh' + 'p_short', 'fixture'), [])

    def test_script_and_style_suffixes_are_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for suffix in ('.js', '.cjs', '.css', '.svg', '.sh'):
                (root / f'asset{suffix}').write_text('/' + 'Users/' + 'fixture/')
            self.assertEqual(len(scanner.scan_tree(root)), 5)

    def test_extracted_non_git_tree_is_scanned_in_full(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'hidden.md').write_text('/' + 'Users/' + 'fixture/')
            self.assertEqual(len(scanner.scan_tree(root)), 1)
