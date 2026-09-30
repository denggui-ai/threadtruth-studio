'use strict';

const search = document.querySelector('#q');
const cases = [...document.querySelectorAll('#case-list > article')];
const count = document.querySelector('#count');
const emptyState = document.querySelector('#empty-state');
const blindButton = document.querySelector('#blind');
const copyStatus = document.querySelector('#copy-status');
const normalize = (value) => value.toLowerCase().trim().replace(/[\s-]+/g, ' ');

function filterCases() {
  const query = normalize(search.value);
  let visible = 0;
  for (const item of cases) {
    const matches = normalize(item.dataset.search).includes(query);
    item.hidden = !matches;
    if (matches) visible += 1;
  }
  count.textContent = `显示 ${visible} / ${cases.length} 个风格 · Showing ${visible} of ${cases.length}`;
  emptyState.hidden = visible > 0;
}

search.addEventListener('input', filterCases);
document.querySelector('#clear-search').addEventListener('click', () => {
  search.value = '';
  filterCases();
  search.focus();
});

blindButton.addEventListener('click', () => {
  const on = document.body.classList.toggle('blind');
  blindButton.setAttribute('aria-pressed', String(on));
  blindButton.textContent = on
    ? '显示路线与结论 / Show routes and verdicts'
    : '隐藏路线与结论 / Hide routes and verdicts';
});

function revealLinkedCase() {
  const target = cases.find((item) => `#${item.id}` === location.hash);
  if (target?.hidden) {
    search.value = '';
    filterCases();
    target.scrollIntoView({ block: 'start' });
  }
}

document.querySelectorAll('.style-shortcuts a').forEach((link) => {
  link.addEventListener('click', () => {
    search.value = '';
    filterCases();
  });
});
window.addEventListener('hashchange', revealLinkedCase);

document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const prompt = document.getElementById(button.dataset.copy);
    const english = button.lang === 'en';
    try {
      await navigator.clipboard.writeText(prompt.textContent);
      button.textContent = english ? 'Copied' : '已复制';
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(prompt);
      selection.removeAllRanges();
      selection.addRange(range);
      button.textContent = english ? 'Selected — copy it manually' : '已选中，请复制';
    }
    copyStatus.textContent = button.textContent;
  });
});

search.value = new URLSearchParams(location.search).get('q') || '';
filterCases();
revealLinkedCase();
