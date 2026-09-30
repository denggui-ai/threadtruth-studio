"""Exercise homepage prompt copying at the browser clipboard and selection boundary."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "gallery/style24-comparison-20260929/prompt-copy.js"

HARNESS = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const options = JSON.parse(process.argv[2]);
const copied = [], targets = new Map(), buttons = [];
let activeElement = null;
const selection = {
  ranges: [{text: 'previous selection'}],
  removeAllRanges() { this.ranges = []; },
  addRange(range) { this.ranges.push(range); }
};
const fixtures = [
  {id: 'home-prompt-zh', lang: 'zh-CN', text: '  请识别服装。\n保留细节与原始换行。\n  ', label: '复制中文指令'},
  {id: 'home-prompt-en', lang: 'en', text: '  Identify this garment.\nKeep every detail & line break.\n  ', label: 'Copy English prompt'}
];
if (!options.empty) {
  for (const fixture of fixtures) {
    const target = {
      id: fixture.id, textContent: fixture.text, tabIndex: 0,
      focus() { activeElement = this; }
    };
    targets.set(target.id, target);
    buttons.push({
      dataset: {copy: target.id}, lang: fixture.lang, textContent: fixture.label,
      listeners: {},
      getAttribute(name) { return name === 'data-copy' || name === 'aria-controls' ? target.id : null; },
      addEventListener(type, listener) { this.listeners[type] = listener; }
    });
  }
}
const status = {textContent: '', lang: 'zh-CN'};
const document = {
  querySelectorAll(selector) {
    assert.equal(selector, '[data-copy]');
    return buttons;
  },
  getElementById(id) { return id === 'home-copy-status' && !options.empty ? status : targets.get(id) || null; },
  createRange() { return {selectNodeContents(node) { this.node = node; }}; }
};
const navigator = {};
if (options.clipboard !== 'missing') {
  navigator.clipboard = {
    async writeText(text) {
      if (options.clipboard === 'rejected') throw new Error('Clipboard permission denied');
      copied.push(text);
    }
  };
}
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), {
  document, navigator, window: {getSelection: () => selection}
});
(async () => {
  if (options.empty) {
    assert.deepEqual(copied, []);
    return;
  }
  const fixture = fixtures.find(item => item.lang === options.lang);
  const button = buttons.find(item => item.lang === options.lang);
  const target = targets.get(fixture.id);
  assert.equal(typeof button.listeners.click, 'function', 'copy button must respond to clicks');
  await button.listeners.click({currentTarget: button, target: button});
  assert.equal(target.textContent, fixture.text, 'copying must not edit the visible prompt');
  if (options.clipboard === 'success') {
    assert.deepEqual(copied, [fixture.text], 'clipboard must receive the complete original prompt');
    assert.equal(activeElement, null, 'successful copying should not move keyboard focus');
    assert.equal(selection.ranges[0].text, 'previous selection');
    const message = options.lang === 'en' ? 'Copied' : '已复制';
    assert.equal(button.textContent, message);
    assert.equal(status.textContent, message, 'assistive technology must receive copy feedback');
  } else {
    assert.deepEqual(copied, []);
    assert.equal(activeElement, target, 'manual-copy fallback must focus the prompt');
    assert.equal(selection.ranges.length, 1, 'manual-copy fallback must replace the old selection');
    assert.equal(selection.ranges[0].node, target, 'manual-copy fallback must select the entire prompt');
    const message = options.lang === 'en' ? 'Selected — copy manually' : '已选中，请手动复制';
    assert.equal(button.textContent, message);
    assert.equal(status.textContent, message, 'fallback must announce that manual copying is required');
  }
  assert.equal(status.lang, fixture.lang, 'live feedback must be pronounced in its language');
  const other = buttons.find(item => item !== button);
  assert.equal(other.textContent, fixtures.find(item => item.lang === other.lang).label);
})().catch(error => { console.error(error); process.exitCode = 1; });
"""


@unittest.skipUnless(shutil.which("node"), "Node is required for browser script checks")
class HomeCopyTests(unittest.TestCase):
    def run_browser(self, **options):
        self.assertTrue(SCRIPT.is_file(), "homepage prompt copy script is missing")
        result = subprocess.run(
            ["node", "-e", HARNESS, str(SCRIPT), json.dumps(options)],
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_both_languages_copy_original_text_and_announce_success(self):
        for lang in ("zh-CN", "en"):
            with self.subTest(lang=lang):
                self.run_browser(clipboard="success", lang=lang)

    def test_missing_clipboard_selects_and_focuses_each_prompt(self):
        for lang in ("zh-CN", "en"):
            with self.subTest(lang=lang):
                self.run_browser(clipboard="missing", lang=lang)

    def test_rejected_clipboard_selects_and_focuses_each_prompt(self):
        for lang in ("zh-CN", "en"):
            with self.subTest(lang=lang):
                self.run_browser(clipboard="rejected", lang=lang)

    def test_page_without_copy_controls_is_safe(self):
        self.run_browser(empty=True, clipboard="missing")


if __name__ == "__main__":
    unittest.main()
