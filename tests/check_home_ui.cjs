// Real browser checks. Run with Playwright on NODE_PATH; optional --screenshots DIR.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const root = path.resolve(__dirname, '../gallery/style24-comparison-20260929');
const mime = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.svg':'image/svg+xml', '.jpg':'image/jpeg', '.webp':'image/webp', '.png':'image/png', '.woff2':'font/woff2', '.json':'application/json'};
const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
const screenshotArg = process.argv.indexOf('--screenshots');
const shots = screenshotArg >= 0 ? path.resolve(process.argv[screenshotArg + 1]) : null;
const failures = [];
async function check(name, fn) {
  try { await fn(); console.log('PASS: ' + name); }
  catch (error) { failures.push(name); console.error('FAIL: ' + name + '\n' + error.stack); }
}
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({headless:true});
  try {
    if (shots) fs.mkdirSync(shots, {recursive:true});
    await check('language switches content, labels and prompt; survives reload', async () => {
      const context = await browser.newContext();
      try {
        const p = await context.newPage(); await p.goto(origin);
        assert.equal(await p.locator('#language-toggle').count(), 1, 'language control missing');
        assert.equal(await p.locator('html').getAttribute('lang'), 'zh-CN');
        assert.equal(await p.locator('#home-prompt-zh').isVisible(), true);
        const zh = await p.locator('#hero-title').innerText();
        const zhAlt = await p.locator('.hero-main img').getAttribute('alt');
        await p.locator('#language-toggle').click();
        assert.equal(await p.locator('html').getAttribute('lang'), 'en');
        assert.notEqual(await p.locator('#hero-title').innerText(), zh);
        assert.notEqual(await p.locator('.hero-main img').getAttribute('alt'), zhAlt);
        assert.equal(await p.locator('#home-prompt-zh').isVisible(), false);
        assert.equal(await p.locator('#home-prompt-en').isVisible(), true);
        assert.equal(await p.locator('[data-lang="zh"]:visible').count(), 0);
        await p.reload(); assert.equal(await p.locator('html').getAttribute('lang'), 'en');
        await p.locator('#language-toggle').click();
        assert.equal(await p.locator('[data-lang="en"]:visible').count(), 0);
      } finally { await context.close(); }
    });
    await check('blocked storage still allows language and lightbox', async () => {
      const context = await browser.newContext();
      try {
        await context.addInitScript(() => { Object.defineProperty(window, 'localStorage', {get() { throw new Error('denied'); }}); });
        const p = await context.newPage(); const errors=[]; p.on('pageerror', e=>errors.push(e.message)); await p.goto(origin);
        assert.equal(await p.locator('#language-toggle').count(), 1);
        await p.locator('#language-toggle').click();
        assert.equal(await p.locator('html').getAttribute('lang'), 'en');
        await p.locator('.highlight-image').first().click();
        assert.equal(await p.locator('#image-dialog').isVisible(), true);
        assert.deepEqual(errors, []);
      } finally { await context.close(); }
    });
    await check('lightbox opens correct image and restores keyboard focus', async () => {
      const context = await browser.newContext();
      try {
        const p = await context.newPage(); await p.goto(origin);
        const link = p.locator('.highlight-image').first();
        const image = await link.getAttribute('href');
        assert.equal(image, 'images/american-street/A.png', 'fallback must open the full original, not a display derivative');
        await link.click();
        assert.equal(await p.locator('#image-dialog').isVisible(), true);
        assert.ok((await p.locator('#dialog-image').getAttribute('src')).endsWith(image));
        assert.ok((await p.locator('#dialog-details').getAttribute('href')).endsWith('compare.html#american-street'));
        await p.keyboard.press('Escape');
        assert.equal(await p.locator('#image-dialog').isVisible(), false);
        assert.equal(await link.evaluate(el => el === document.activeElement), true);
        await link.click(); await p.locator('#dialog-close').click();
        assert.equal(await link.evaluate(el => el === document.activeElement), true);
      } finally { await context.close(); }
    });
    for (const mode of ['success', 'rejected']) {
      await check('copy prompts and page link: ' + mode, async () => {
        const context = await browser.newContext();
        try {
          await context.addInitScript(mode => { window.copied=[]; Object.defineProperty(navigator, 'clipboard', {value:{writeText:async text=>{ if(mode==='rejected') throw new Error('denied'); window.copied.push(text); }}}); }, mode);
          const p = await context.newPage(); await p.goto(origin);
          const prompt = p.locator('#home-prompt-zh'); const content = await prompt.textContent();
          await p.locator('[data-copy="home-prompt-zh"]').click();
          if(mode==='success') assert.deepEqual(await p.evaluate(()=>window.copied), [content]);
          else assert.equal(await p.evaluate(()=>window.getSelection().toString()), content);
          await p.locator('#language-toggle').click();
          assert.equal(await p.locator('#home-copy-status').innerText(), '', 'old-language feedback must clear');
          const en = await p.locator('#home-prompt-en').textContent();
          await p.locator('[data-copy="home-prompt-en"]').click();
          if(mode==='success') assert.equal(await p.evaluate(()=>window.copied.at(-1)), en);
          else assert.equal(await p.evaluate(()=>window.getSelection().toString()), en);
          await p.locator('#copy-page-link').click();
          if(mode==='success') assert.equal(await p.evaluate(()=>window.copied.at(-1)), origin + '/#begin');
          else {
            assert.equal(await p.locator('#page-link-fallback').isVisible(), true);
            assert.equal(await p.locator('#page-link-fallback').inputValue(), origin + '/#begin');
          }
        } finally { await context.close(); }
      });
    }
    for (const outcome of ['resolve', 'reject']) {
      await check('language change cancels stale clipboard feedback: ' + outcome, async () => {
        const context = await browser.newContext();
        try {
          await context.addInitScript(() => {
            Object.defineProperty(navigator, 'clipboard', {value:{writeText:()=>new Promise((resolve,reject)=>{
              window.pendingCopy={resolve,reject};
            })}});
          });
          const p=await context.newPage(); await p.goto(origin);
          if (outcome === 'reject') await p.locator('#language-toggle').click();
          const from = outcome === 'resolve' ? 'zh' : 'en';
          await p.locator(`[data-copy="home-prompt-${from}"]`).click();
          await p.locator('#language-toggle').click();
          await p.evaluate(outcome => window.pendingCopy[outcome](), outcome);
          assert.equal(await p.locator('#home-copy-status').innerText(), '', 'stale feedback reappeared after language switch');
          assert.equal(await p.evaluate(()=>window.getSelection().toString()), '');
          assert.equal(await p.locator('#language-toggle').evaluate(el=>el===document.activeElement),true,'stale fallback moved focus');
          // The new language remains fully usable after the stale operation is ignored.
          const to = from === 'zh' ? 'en' : 'zh';
          await p.locator(`[data-copy="home-prompt-${to}"]`).click();
          await p.evaluate(()=>window.pendingCopy.resolve());
          assert.equal(await p.locator('#home-copy-status').innerText(),to==='en'?'Copied':'已复制');
        } finally { await context.close(); }
      });
    }
    await check('no JavaScript: Chinese content, all styles and original links remain usable', async () => {
      const context = await browser.newContext({javaScriptEnabled:false});
      try {
        const p=await context.newPage(); await p.goto(origin);
        assert.equal(await p.locator('.highlight-image').count(), 24);
        assert.equal(await p.locator('[data-lang="en"]:visible').count(), 0);
        assert.equal(await p.locator('#home-prompt-zh').isVisible(), true);
        assert.equal(await p.locator('#language-toggle').isVisible(), false);
        assert.equal(await p.locator('#copy-page-link').isVisible(), false);
        assert.equal(await p.locator('#image-dialog').isVisible(), false);
        assert.ok(/\.png$/.test(await p.locator('.highlight-image').first().getAttribute('href')));
      } finally { await context.close(); }
    });
    await check('legacy links redirect with query; new section links stay on home', async () => {
      const p=await browser.newPage();
      try {
        await p.goto(origin + '/?source=readme#old-money');
        await p.waitForURL('**/compare.html?source=readme#old-money');
        for(const hash of ['complete-case','style-highlights','outfit','begin','shoot-options','capabilities']) {
          await p.goto(origin + '/#' + hash);
          assert.equal(new URL(p.url()).pathname, '/');
          assert.equal(await p.locator('#' + hash).count(), 1);
        }
      } finally { await p.close(); }
    });
    await check('comparison page search, blind view and narrow layout still work', async () => {
      const p = await browser.newPage();
      try {
        await p.goto(origin + '/compare.html');
        await p.locator('#q').fill('老钱');
        assert.equal(await p.locator('#case-list > article:visible').count(), 1);
        assert.equal(await p.locator('#old-money').isVisible(), true);
        await p.locator('#q').fill('no-matching-style');
        assert.equal(await p.locator('#empty-state').isVisible(), true);
        await p.locator('#clear-search').click();
        assert.equal(await p.locator('#case-list > article:visible').count(), 24);
        await p.locator('#blind').click();
        assert.equal(await p.locator('.reveal:visible').count(), 0);
        await p.locator('#blind').click();
        for (const width of [1440,390,320]) {
          await p.setViewportSize({width,height:1000});
          assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'comparison overflow '+width);
          if (shots) {
            await p.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
            await p.screenshot({path:path.join(shots,`compare-${width}.png`)});
          }
        }
      } finally { await p.close(); }
    });
    await check('jacket comparison preserves input, external originals and disclosed sixth pose', async () => {
      const p=await browser.newPage(); const errors=[]; p.on('pageerror',e=>errors.push(e.message));
      try {
        await p.goto(origin+'/reviewed-cases.html#black-jacket-office');
        const records=await (await p.request.get(origin+'/reviewed-cases.json')).json();
        const office=records.cases.find(c=>c.id==='black-jacket-office');
        const external=records.cases.find(c=>c.id==='external-black-leather');
        assert.equal(office.input_image.sha256,external.input_image.sha256);
        assert.equal(office.images[5].actual_pose,'FRONT_RELAXED_STANDING');
        assert.equal(await p.locator('#black-jacket-office .outfit-comparison img').count(),3);
        assert.equal(await p.locator('#black-jacket-office .reviewed-images img').count(),6);
        assert.equal(await p.locator('#external-black-leather .reviewed-images img').count(),6);
        const originals=await p.locator('#black-jacket-office .reviewed-images a').evaluateAll(as=>as.map(a=>a.getAttribute('href')));
        assert.deepEqual(originals,office.images.map(i=>i.path));
        await p.locator('#black-jacket-office img').evaluateAll(imgs=>imgs.forEach(i=>i.loading='eager'));
        await p.waitForFunction(()=>[...document.querySelectorAll('#black-jacket-office img')].every(i=>i.complete&&i.naturalWidth>0));
        for(const lang of ['zh','en']) {
          if(lang==='en') await p.locator('#case-language-toggle').click();
          assert.match(await p.locator('#black-jacket-office').innerText(),lang==='zh'?/第六张采用正面自然站姿/:/slot 6 uses stationary frontal standing/);
          for(const width of [1440,390,320]) {
            await p.setViewportSize({width,height:1000});
            assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
            const columns=await p.locator('.outfit-comparison').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
            assert.equal(columns,width>600?3:1);
            assert.equal(await p.locator('.outfit-comparison img').first().evaluate(el=>getComputedStyle(el).objectFit),'contain');
            if(shots&&width!==320) {
              await p.locator('.outfit-comparison').screenshot({path:path.join(shots,`jacket-comparison-${lang}-${width}.png`)});
              if(width===1440) await p.locator('#black-jacket-office .reviewed-images').screenshot({path:path.join(shots,`jacket-six-${lang}-${width}.png`)});
            }
          }
        }
        assert.deepEqual(errors,[]);
      } finally {await p.close();}
    });
    await check('responsive Chinese and English layouts, complete images and no page errors', async () => {
      const context=await browser.newContext();
      try {
        const p=await context.newPage(); const errors=[]; p.on('pageerror',e=>errors.push(e.message));
        await p.goto(origin); await p.locator('img').evaluateAll(imgs=>imgs.forEach(i=>i.loading='eager'));
        await p.waitForFunction(()=>[...document.images].filter(i=>i.getAttribute('src')).every(i=>i.complete&&i.naturalWidth>0));
        await p.evaluate(()=>document.fonts.ready);
        for(const lang of ['zh','en']) {
          if(lang==='en') await p.locator('#language-toggle').click();
          for(const width of [1440,1024,768,390,320]) {
            await p.setViewportSize({width,height:1000});
            assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'overflow '+lang+' '+width);
            assert.equal(await p.locator('.highlight-image:visible').count(),24);
            const columns=await p.locator('.highlights-grid').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
            assert.equal(columns,width>=1100?4:width>=700?3:2);
            assert.equal(await p.locator('.pose-gallery img').count(),6);
            const caseCards=await p.locator('.reviewed-card').evaluateAll(cards=>cards.map(card=>{const r=card.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width};}));
            assert.equal(caseCards.length,5,'five cases must remain accessible');
            assert.equal(await p.locator('#home-before-after img').count(),3,'source/result feature missing');
            assert.ok((await p.locator('.reviewed-card img').nth(2).getAttribute('src')).endsWith('green-shirt-home/look-1.png'),'home cover must show the full outfit');
            if(width>900) assert.ok(caseCards.every(card=>Math.abs(card.y-caseCards[0].y)<1),'desktop cases must share one row');
            if(width>480&&width<=900) assert.ok(Math.abs(caseCards[4].x+caseCards[4].width/2-width/2)<1,'tablet last case must be centered');
            const caseImageSizes=await p.locator('.reviewed-card img').evaluateAll(imgs=>imgs.map(i=>({width:i.getBoundingClientRect().width,height:i.getBoundingClientRect().height})));
            assert.ok(caseImageSizes.every(i=>Math.abs(i.width/i.height-2/3)<.01),'case covers must keep their full portrait proportions');
            if(shots&&[1440,768,390].includes(width)) await p.locator('#reviewed-cases').screenshot({path:path.join(shots,`cases-${lang}-${width}.png`)});

            if(shots) {
              await p.evaluate(()=>scrollTo({top:0,behavior:"instant"})); await p.screenshot({path:path.join(shots,`home-${lang}-${width}.png`)});
              if(lang==='zh'&&[1440,390].includes(width)) {
                await p.screenshot({path:path.join(shots,`full-${width}.png`),fullPage:true});
                for(const section of ['complete-case','outfit','style-highlights','begin']) {
                  await p.locator('#'+section).evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
                  await p.screenshot({path:path.join(shots,`${section}-${width}.png`)});
                }
              }
            }
          }
        }
        assert.deepEqual(errors,[]);
      } finally { await context.close(); }
    });
  } finally { await browser.close(); await new Promise(resolve=>server.close(resolve)); }
  if(failures.length) throw new Error(failures.length + ' browser checks failed: ' + failures.join('; '));
})().catch(error=>{ console.error(error.message); server.close(); process.exitCode=1; });
