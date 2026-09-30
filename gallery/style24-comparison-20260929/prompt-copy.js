/* Copy the homepage recognition prompts. */
(() => {
  const status = document.getElementById('home-copy-status');
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const prompt = document.getElementById(button.dataset.copy);
      if (!prompt) return;
      const english = button.lang === 'en';
      let message;
      try {
        await navigator.clipboard.writeText(prompt.textContent);
        message = english ? 'Copied' : '已复制';
      } catch {
        prompt.focus();
        const range = document.createRange();
        range.selectNodeContents(prompt);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        message = english ? 'Selected — copy manually' : '已选中，请手动复制';
      }
      button.textContent = message;
      if (status) {
        status.lang = button.lang;
        status.textContent = message;
      }
    });
  });
})();
