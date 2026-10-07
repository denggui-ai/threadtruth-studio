#!/usr/bin/env node
// Development-only export of the same SVG. Connects to the dedicated CDP browser.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '../..');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9344');
  const page = await browser.contexts()[0].newPage();
  try {
    await page.setViewportSize({ width: 2400, height: 1900 });
    await page.setContent('<style>body{margin:0;overflow:hidden}</style>' + fs.readFileSync(path.join(root, 'docs/assets/architecture-overview.svg'), 'utf8'));
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.locator('svg text').evaluateAll(elements => elements
      .filter(element => element.getComputedTextLength() > Number(element.dataset.maxwidth) + 1)
      .map(element => element.textContent));
    if (overflow.length) throw new Error(`Text exceeds panel width: ${overflow.join('; ')}`);
    await page.locator('svg').screenshot({ path: path.join(root, 'docs/assets/architecture-overview.png') });
    console.log('Text bounds PASS; same-source SVG exported to 2400 × 1900 PNG');
  } finally {
    await page.close();
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
