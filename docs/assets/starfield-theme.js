/* Apply the saved appearance before styles paint, including the reader dialog. */
(() => {
  'use strict';
  const key = 'starfield-archive-theme';
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let saved = null;
  try { saved = localStorage.getItem(key); } catch (_) {}
  if (!['light', 'dark'].includes(saved)) saved = null;
  function apply(theme) {
    const dark = theme === 'dark';
    document.documentElement.dataset.theme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = dark ? '#101923' : '#e9e7df';
    const button = document.getElementById('themeToggle');
    if (button) {
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', (dark ? '라이트' : '다크') + ' 모드로 변경');
      button.querySelector('[data-theme-label]').textContent = dark ? '라이트 모드' : '다크 모드';
    }
  }
  apply(saved || (system.matches ? 'dark' : 'light'));
  document.addEventListener('DOMContentLoaded', () => {
    apply(document.documentElement.dataset.theme);
    document.getElementById('themeToggle').addEventListener('click', () => {
      saved = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(saved);
      try { localStorage.setItem(key, saved); } catch (_) {}
    });
  });
  system.addEventListener('change', event => {
    if (!saved) apply(event.matches ? 'dark' : 'light');
  });
})();
