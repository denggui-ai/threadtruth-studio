/* Retain the public gallery's original deep links after the homepage split. */
(() => {
  const legacy = new Set([
    'cases', 'american-street', 'athleisure', 'balletcore', 'british-heritage',
    'cityboy', 'clean-fit', 'coquette-ladylike', 'ecommerce-studio',
    'french-effortless', 'gorpcore', 'guochao-street', 'italian-luxe',
    'japanese-lifestyle', 'korean-cold-editorial', 'korean-menswear',
    'neo-chinese', 'nordic-minimal', 'office-commute-women', 'old-money',
    'preppy', 'quiet-luxury', 'resort-vacation', 'workwear-vintage', 'y2k-millennium'
  ]);
  function forwardLegacyLink() {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); }
    catch { return; }
    if (legacy.has(hash)) location.replace('compare.html' + location.search + '#' + encodeURIComponent(hash));
  }
  forwardLegacyLink();
  window.addEventListener('hashchange', forwardLegacyLink);
})();

/* Progressive homepage enhancements; direct links and Chinese copy work without JS. */
(() => {
  if (typeof document === 'undefined' || !document.querySelector('.home-page')) return;
  const root = document.documentElement;
  const toggle = document.getElementById('language-toggle');
  const storageKey = 'threadtruth-language';
  let language = 'zh';
  try { if (localStorage.getItem(storageKey) === 'en') language = 'en'; } catch { /* Storage is optional. */ }
  const dialog = document.getElementById('image-dialog');
  const dialogImage = document.getElementById('dialog-image');
  const dialogCaption = document.getElementById('dialog-caption');
  let opener = null;
  const promptButtons = [...document.querySelectorAll('[data-copy]')];
  const promptLabels = new Map(promptButtons.map(button => [button, button.textContent]));

  function applyLanguage() {
    root.dataset.language = language;
    root.lang = language === 'en' ? 'en' : 'zh-CN';
    document.title = language === 'en' ? 'Caiguang · Your garments. A new perspective.' : '裁光 · 你的衣服。下一组大片。';
    toggle.textContent = language === 'en' ? '中文' : 'EN';
    toggle.lang = language === 'en' ? 'zh-CN' : 'en';
    toggle.setAttribute('aria-label', language === 'en' ? '切换为中文' : 'Switch to English');
    for (const attr of ['alt', 'aria-label']) {
      document.querySelectorAll(`[data-${attr}-${language}]`).forEach(element => {
        element.setAttribute(attr, element.getAttribute(`data-${attr}-${language}`));
      });
    }
    document.querySelectorAll('.install-guide').forEach(link => {
      link.hash = language === 'en' ? 'english' : '简体中文';
    });
    document.querySelectorAll('.troubleshoot-link').forEach(link => {
      link.hash = language === 'en' ? 'troubleshooting' : '安装排查';
    });
    promptButtons.forEach(button => { button.textContent = promptLabels.get(button); });
    document.getElementById('home-copy-status').textContent = '';
    document.getElementById('page-copy-status').textContent = '';
    document.dispatchEvent(new Event('threadtruth:languagechange'));
    if (opener && dialog.open) updateDialog();
  }
  toggle.addEventListener('click', () => {
    language = language === 'en' ? 'zh' : 'en';
    applyLanguage();
    try { localStorage.setItem(storageKey, language); } catch { /* Switching still works. */ }
  });
  applyLanguage();
  root.classList.add('has-js');

  function updateDialog() {
    const image = opener.querySelector('img');
    dialogImage.src = opener.href;
    dialogImage.alt = image.alt;
    dialogCaption.textContent = image.alt;
    document.getElementById('dialog-details').href = opener.dataset.details;
    document.getElementById('dialog-original').href = opener.href;
  }
  if (dialog && typeof dialog.showModal === 'function') {
    document.querySelectorAll('[data-lightbox]').forEach(link => {
      link.addEventListener('click', event => {
        // Preserve browser gestures for opening the original image in another tab.
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        opener = link;
        updateDialog();
        dialog.showModal();
        root.classList.add('image-open');
        document.getElementById('dialog-close').focus();
      });
    });
    document.getElementById('dialog-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => {
      root.classList.remove('image-open');
      if (opener) opener.focus({preventScroll:true});
    });
    dialog.addEventListener('click', event => {
      const box = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) dialog.close();
    });
  }

  const pageStatus = document.getElementById('page-copy-status');
  const pageFallback = document.getElementById('page-link-fallback');
  document.getElementById('copy-page-link').addEventListener('click', async () => {
    // Use the current deployment path, without tracking queries or a previous style hash.
    const url = new URL(location.href);
    url.search = '';
    url.hash = 'begin';
    try {
      await navigator.clipboard.writeText(url.href);
      pageFallback.hidden = true;
      pageStatus.textContent = language === 'en' ? 'Link copied. Continue on your computer.' : '链接已复制，可稍后在电脑上继续。';
    } catch {
      pageFallback.hidden = false;
      pageFallback.value = url.href;
      pageFallback.focus();
      pageFallback.select();
      pageStatus.textContent = language === 'en' ? 'Select and copy the link below manually.' : '请手动复制下方链接。';
    }
    pageStatus.lang = root.lang;
  });
})();
