"""Exercise legacy gallery links with a minimal browser location, without a DOM."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery/style24-comparison-20260929"


@unittest.skipUnless(shutil.which("node"), "Node is required for browser script checks")
class ShowcaseNavigationTests(unittest.TestCase):
    def test_legacy_links_redirect_without_swallowing_new_home_sections(self):
        script = GALLERY / "home.js"
        self.assertTrue(script.is_file(), "homepage compatibility script is missing")
        harness = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const code = fs.readFileSync(process.argv[1], 'utf8');
const ids = [...fs.readFileSync(process.argv[2], 'utf8').matchAll(/<article\b[^>]*\bid="([^"]+)"/g)].map(m => m[1]);
assert.equal(ids.length, 24);
for (const id of ['cases', ...ids]) {
  let target;
  const location = {hash: '#' + id, search: '?source=readme', replace: v => target = v};
  const listeners = {};
  vm.runInNewContext(code, {location, window: {addEventListener: (k,v) => listeners[k] = v}});
  assert.equal(target, 'compare.html?source=readme#' + id);
}
for (const hash of ['', '#complete-case', '#style-highlights', '#outfit', '#begin', '#unknown', '#%E0%A4%A']) {
  let target;
  const location = {hash, search: '', replace: v => target = v};
  const listeners = {};
  vm.runInNewContext(code, {location, window: {addEventListener: (k,v) => listeners[k] = v}});
  assert.equal(target, undefined);
  location.hash = '#old-money';
  listeners.hashchange();
  assert.equal(target, 'compare.html#old-money');
}
"""
        result = subprocess.run(["node", "-e", harness, str(script), str(GALLERY / "compare.html")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
