// Render existing HTML templates and licensed local assets; no network or AI generation.
// Run after brand_assets.py build, before brand_assets.py manifest, with Playwright on NODE_PATH.
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const gallery = path.join(root, 'gallery/style24-comparison-20260929');
const mime = {'.html':'text/html', '.jpg':'image/jpeg', '.svg':'image/svg+xml', '.woff2':'font/woff2'};
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1200,height:630},deviceScaleFactor:1});
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== 'http://threadtruth-preview.invalid') return route.abort();
      const relative = decodeURIComponent(url.pathname).slice(1);
      const base = ['og-home.html','og-compare.html'].includes(relative) ? path.join(root, 'tools/brand_cards') : gallery;
      const file = path.resolve(base, relative);
      if (!file.startsWith(base + path.sep) || !fs.existsSync(file)) return route.fulfill({status:404,body:'Not found'});
      await route.fulfill({path:file,contentType:mime[path.extname(file)] || 'application/octet-stream'});
    });
    for (const name of ['og-home','og-compare']) {
      await page.goto('http://threadtruth-preview.invalid/' + name + '.html');
      await page.evaluate(()=>document.fonts.ready);
      await page.waitForFunction(()=>[...document.images].every(image=>image.complete&&image.naturalWidth>0));
      await page.screenshot({path:path.join(gallery, 'assets/brand', name + '.png')});
      console.log('Rendered ' + name + '.png (1200 × 630)');
    }
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
