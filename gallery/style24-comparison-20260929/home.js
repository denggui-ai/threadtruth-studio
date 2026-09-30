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
