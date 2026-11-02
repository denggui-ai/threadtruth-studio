/* Preset teaching examples only. No model, upload, task access or runtime ranking. */
(() => {
  const root = document.documentElement;
  const family = document.getElementById('pose-family');
  if (!family) return;
  const view = document.getElementById('pose-view');
  const all = document.getElementById('pose-show-all');
  const count = document.getElementById('pose-count');
  const library = [...document.querySelectorAll('.library-pose')];
  const history = document.getElementById('demo-history');
  const candidates = document.querySelector('.demo-candidates');
  const demo = [...candidates.children];
  const text = (zh, en) => root.dataset.language === 'en' ? en : zh;
  let expanded = false;
  const scenarios = {
    neck: {
      order: ['stand-neutral', 'stand-weight-shift', 'close-ear-tuck'],
      note: ['领口示例：先让手离开领缘，再核对袖部和商品角度。', 'Neckline example: keep hands away from the collar, then check sleeves and garment views.']
    },
    waist: {
      order: ['stand-neutral', 'stand-weight-shift', 'turn-front-counter'],
      note: ['腰腹示例：手臂与腰腹分开。受限推袖不进入候选；转身需前侧商品素材。', 'Waist example: keep arms clear of the abdomen. The restricted sleeve push is excluded; turns require front-side garment references.']
    },
    shape: {
      order: ['walk-pause', 'stand-neutral', 'stand-wide-anchor'],
      note: ['轮廓示例：用全身站姿或小步看线条；先核对裤裙的步幅与活动量。', 'Silhouette example: try a full-body stance or small step, after checking the garment’s movement allowance.']
    }
  };
  function filterLibrary() {
    const matching = library.filter(card => (family.value === 'all' || card.dataset.family === family.value) && (view.value === 'all' || card.dataset.view === view.value));
    const visible = expanded ? matching : matching.slice(0, 12);
    library.forEach(card => { card.hidden = !visible.includes(card); });
    count.textContent = text(`显示 ${visible.length} / ${matching.length} 个视图`, `Showing ${visible.length} / ${matching.length} views`);
    document.getElementById('pose-empty').hidden = matching.length > 0;
    all.hidden = matching.length <= 12;
    all.textContent = expanded ? text('收起图库 ↑', 'Show fewer ↑') : text(`展开全部 ${matching.length} 视图 ↓`, `Show all ${matching.length} views ↓`);
  }
  function updateDemo() {
    const goal = document.querySelector('[name="demo-goal"]:checked').value;
    const scenario = scenarios[goal];
    let order = [...scenario.order];
    const repeats = history.checked ? {'stand-neutral':'exact', 'stand-weight-shift':'near'} : {};
    // Move illustrated repeats after the other examples, preserving the preset order.
    if (history.checked) order = order.filter(id => !repeats[id]).concat(order.filter(id => repeats[id]));
    demo.forEach(card => { card.hidden = !order.includes(card.dataset.demoPose); });
    order.forEach((id, index) => {
      const card = demo.find(item => item.dataset.demoPose === id);
      const repeat = repeats[id] || '';
      card.dataset.repeat = repeat;
      card.querySelector('.demo-order').textContent = String(index + 1).padStart(2, '0');
      card.querySelector('.demo-state').textContent = repeat === 'exact' ? text('同动作 · 需避重', 'Exact · revisit') : repeat === 'near' ? text('疑似近似 · 需复核', 'Near · review') : text('可优先考虑', 'Consider first');
      candidates.append(card);
    });
    document.querySelector('.source-frame').dataset.demoFocus = goal;
    document.getElementById('demo-goal-note').textContent = text(...scenario.note);
    document.getElementById('demo-history-records').hidden = !history.checked;
    const repeatCount = order.filter(id => repeats[id]).length;
    document.getElementById('demo-result').textContent = history.checked
      ? text(`示例对照：${repeatCount} 个候选需避重或复核，已移到后面；其余候选仍需核对商品条件。`, `Example comparison: ${repeatCount} candidate(s) moved back for repeat review. Check garment conditions for every remaining option.`)
      : text('示例候选 3 个 · 先核对条件，再决定是否选用。', '3 example candidates · check their conditions before choosing.');
  }
  function languageChanged() {
    document.querySelectorAll('#pose-library option').forEach(option => {
      option.textContent = text(option.dataset.labelZh, option.dataset.labelEn);
    });
    filterLibrary();
    updateDemo();
  }
  [family, view].forEach(select => select.addEventListener('change', () => { expanded = false; filterLibrary(); }));
  all.addEventListener('click', () => {
    expanded = !expanded;
    filterLibrary();
    if (!expanded) document.querySelector('.pose-filter-bar').scrollIntoView({behavior:'instant',block:'start'});
  });
  document.querySelectorAll('[name="demo-goal"]').forEach(input => input.addEventListener('change', updateDemo));
  history.addEventListener('change', updateDemo);
  document.addEventListener('threadtruth:languagechange', languageChanged);
  languageChanged();
})();
