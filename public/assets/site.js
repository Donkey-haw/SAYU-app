// SAYU site script. No tracking, no cookies.
const SAYU = {
  // Set when the trial DMG is published on GitHub Releases.
  downloadURL: 'https://github.com/Donkey-haw/SAYU-app/releases/download/v0.11.3/SAYU-0.11.3.dmg',
  version: '0.11.3 체험판',
  size: '378MB',
};

const nav = document.getElementById('nav');
const onScroll = () => nav && nav.classList.toggle('scrolled', scrollY > 4);
addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Download buttons: a working link once the file is published, an honest
// "preparing" state until then.
document.querySelectorAll('[data-download]').forEach((el) => {
  if (SAYU.downloadURL) {
    el.href = SAYU.downloadURL;
  } else if (el.dataset.download === 'primary') {
    el.setAttribute('aria-disabled', 'true');
    el.removeAttribute('href');
    const label = el.querySelector('[data-label]');
    if (label) label.textContent = '체험판 파일 준비 중';
  }
});
document.querySelectorAll('[data-version]').forEach((el) => {
  el.textContent = SAYU.downloadURL ? `${SAYU.version} · ${SAYU.size} · Apple Silicon` : `${SAYU.version} · 파일을 올리면 이곳에서 바로 받을 수 있습니다`;
});

// The hero's one authored moment: the AI's work steps advance in place, the
// way the app shows them, and the board columns fill in when they finish.
const win = document.querySelector('.window[data-play]');
if (win) {
  const trace = win.querySelector('.trace');
  const head = trace.querySelector('[data-step]');
  const clock = trace.querySelector('[data-clock]');
  const items = [...trace.querySelectorAll('li')];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finish = () => {
    items.forEach((li) => { li.classList.add('ok'); li.classList.remove('now'); });
    trace.classList.add('done');
    head.textContent = `작업 ${items.length}단계`;
    clock.textContent = '0:47';
  };
  if (reduce) { finish(); } else {
    let i = 0, seconds = 0;
    items.forEach((li) => li.classList.remove('ok'));
    trace.classList.remove('done');
    let tick;
    const step = () => {
      items.forEach((li, n) => { li.classList.toggle('ok', n < i); li.classList.toggle('now', n === i); });
      if (i < items.length) { head.textContent = `${items[i].dataset.label} 중…`; i += 1; setTimeout(step, 1100); }
      else { clearInterval(tick); finish(); win.classList.add('playing'); }
    };
    const start = () => {
      tick = setInterval(() => { seconds += 1; clock.textContent = `0:${String(Math.min(seconds, 59)).padStart(2, '0')}`; }, 120);
      step();
    };
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { io.disconnect(); start(); }
    }, { threshold: 0.4 });
    io.observe(win);
  }
}

// Reading pages: highlight the section in view.
const links = [...document.querySelectorAll('.doc-nav a[href^="#"]')];
if (links.length) {
  const map = new Map(links.map((a) => [a.getAttribute('href').slice(1), a]));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { links.forEach((a) => a.classList.remove('active')); map.get(e.target.id)?.classList.add('active'); }
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  map.forEach((_, id) => { const el = document.getElementById(id); if (el) io.observe(el); });
}
