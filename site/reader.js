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
  var idx = 0, playing = false, cur = null;
  var sel = document.getElementById('voice'), rate = document.getElementById('rate');
  function score(v) {
    var n = v.name;
    if (/natural|online|neural/i.test(n)) return 4;          // нейросетевые голоса Edge и Windows
    if (/premium|enhanced|улучш|siri/i.test(n)) return 3;      // улучшенные голоса Apple
    if (/google/i.test(n)) return 2;
    return v.localService ? 0 : 1;
  }
  function voices() {
    return synth.getVoices().filter(function (v) { return /^ru/i.test(v.lang); })
      .sort(function (a, b) { return score(b) - score(a); });
  }
  function voice() {
    var vs = voices(), want = read('voice');
    return vs.find(function (v) { return v.name === want; }) || vs[0];
  }
  function fill() {
    var vs = voices(), cur = voice();
    sel.innerHTML = '';
    vs.forEach(function (v) {
      var o = document.createElement('option'); o.value = v.name;
      o.textContent = v.name.replace(/^Microsoft\s+|\s*\(.*\)$|\s*-\s*Russian.*$/g, '') + (score(v) >= 3 ? ' *' : '');
      if (cur && v.name === cur.name) o.selected = true; sel.appendChild(o);
    });
    sel.hidden = vs.length < 2;
  }
  sel.onchange = function () { store('voice', sel.value); restart() };
  // смена голоса или скорости: перечитать текущий абзац заново
  function restart() { if (playing) { cur = null; synth.cancel(); setTimeout(speak, 60); } }
  rate.value = read('rate') || '1';
  rate.onchange = function () { store('rate', rate.value); restart() };
  function mark(i) {
    paras.forEach(function (p) { p.classList.remove('speaking'); });
    if (paras[i]) { paras[i].classList.add('speaking'); paras[i].scrollIntoView({ block: 'center', behavior: 'smooth' }); }
  }
  function speak() {
    if (!playing || idx >= paras.length) { stop(); return; }
    var u = new SpeechSynthesisUtterance(paras[idx].textContent);
    var v = voice(); if (v) u.voice = v; u.lang = 'ru-RU'; u.rate = parseFloat(rate.value) || 1;
    cur = u; u.onend = function () { if (playing && cur === u) { idx++; speak(); } };
    mark(idx); synth.speak(u);
  }
  function stop() { playing = false; synth.cancel(); btn.textContent = 'Слушать'; btn.setAttribute('aria-pressed', 'false'); mark(-1); }
  function show() { if (voice()) { btn.hidden = false; rate.hidden = false; fill(); } }
  show(); synth.onvoiceschanged = show;
  btn.onclick = function () {
    if (playing) { stop(); return; }
    // начинать с абзаца, который сейчас на экране
    idx = Math.max(0, paras.findIndex(function (p) { return p.getBoundingClientRect().bottom > 80; }));
    playing = true; btn.textContent = 'Пауза'; btn.setAttribute('aria-pressed', 'true'); speak();
  };
  addEventListener('pagehide', function () { synth.cancel(); });
})();
