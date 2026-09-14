const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');
if (toggle && nav) {
  const closeMenu = () => { nav.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); };
  toggle.addEventListener('click', () => {
    const opened = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(opened));
  });
  nav.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('is-open')) { closeMenu(); toggle.focus(); } });
}
if (navigator.clipboard && window.isSecureContext) {
  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'copy-button'; button.textContent = '複製';
    button.setAttribute('aria-label', '複製這段指令');
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); button.textContent = '已複製'; }
      catch { button.textContent = '請選取文字複製'; }
    });
    pre.prepend(button);
  });
}
