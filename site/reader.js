(function () {
  var root = document.documentElement;
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function read(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  var art = document.querySelector('.chapter');
  // Отметки прочитанного и «продолжить чтение» на главной
  var last = read('last');
  document.querySelectorAll('.toc a').forEach(function (a) {
    var slug = a.getAttribute('href').replace('.html', '');
    if (read('done:' + slug)) a.classList.add('read');
  });
  var cont = document.getElementById('continue');
  if (cont && last) { cont.href = last + '.html'; cont.textContent = 'Продолжить чтение'; }

  if (!art) return;
  var slug = art.dataset.slug;
  store('last', slug);

  var bar = document.getElementById('bar');
  function onScroll() {
    var h = document.documentElement.scrollHeight - innerHeight;
    var p = h > 0 ? scrollY / h : 1;
    bar.style.width = (p * 100) + '%';
    if (p > 0.95) store('done:' + slug, '1');
  }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // Размер шрифта
  function size(d) {
    var cur = parseFloat(getComputedStyle(root).getPropertyValue('--fs')) || 20;
    var n = Math.min(28, Math.max(15, cur + d));
    root.style.setProperty('--fs', n + 'px'); store('font', n);
  }
  document.getElementById('font-').onclick = function () { size(-1); };
  document.getElementById('font+').onclick = function () { size(1); };

  // Тема
  document.getElementById('theme').onclick = function () {
    var dark = root.dataset.theme ? root.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark'; store('theme', root.dataset.theme);
  };

  // Чтение вслух голосом устройства
  var btn = document.getElementById('listen');
  if (!('speechSynthesis' in window)) return;
  var synth = speechSynthesis, paras = Array.prototype.slice.call(art.querySelectorAll('h1, p:not(.num)'));
  var idx = 0, playing = false;
  function voice() {
    var vs = synth.getVoices().filter(function (v) { return /^ru/i.test(v.lang); });
    return vs.find(function (v) { return /natural|google|milena|yuri|dmitry|svetlana/i.test(v.name); }) || vs[0];
  }
  function mark(i) {
    paras.forEach(function (p) { p.classList.remove('speaking'); });
    if (paras[i]) { paras[i].classList.add('speaking'); paras[i].scrollIntoView({ block: 'center', behavior: 'smooth' }); }
  }
  function speak() {
    if (!playing || idx >= paras.length) { stop(); return; }
    var u = new SpeechSynthesisUtterance(paras[idx].textContent);
    var v = voice(); if (v) u.voice = v; u.lang = 'ru-RU'; u.rate = 1;
    u.onend = function () { if (playing) { idx++; speak(); } };
    mark(idx); synth.speak(u);
  }
  function stop() { playing = false; synth.cancel(); btn.textContent = 'Слушать'; btn.setAttribute('aria-pressed', 'false'); mark(-1); }
  function show() { if (voice()) btn.hidden = false; }
  show(); synth.onvoiceschanged = show;
  btn.onclick = function () {
    if (playing) { stop(); return; }
    // начинать с абзаца, который сейчас на экране
    idx = Math.max(0, paras.findIndex(function (p) { return p.getBoundingClientRect().bottom > 80; }));
    playing = true; btn.textContent = 'Пауза'; btn.setAttribute('aria-pressed', 'true'); speak();
  };
  addEventListener('pagehide', function () { synth.cancel(); });
})();
