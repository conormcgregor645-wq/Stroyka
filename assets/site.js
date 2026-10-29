/* Общий код всех страниц: Яндекс Метрика и реклама РСЯ. */
(function () {
  "use strict";

  /* ===== НАСТРОЙКИ — замените заглушки ===== */
  var metrikaId = "113822395";   // номер счётчика Метрики, например "98765432"
  var rsyBlockId = "RSY_BLOCK_ID"; // ID блока РСЯ, например "R-A-1234567-1"

  /* ---------- Яндекс Метрика ---------- */

  var metrikaOn = /^\d+$/.test(metrikaId);
  if (metrikaOn) {
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      for (var j = 0; j < document.scripts.length; j++) { if (document.scripts[j].src === r) return; }
      k = e.createElement(t); a = e.getElementsByTagName(t)[0]; k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
    })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
    window.ym(Number(metrikaId), "init", {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: true
    });
  }

  // Цели: calc_done — выполнен расчёт, affiliate_click — клик по ссылке магазина.
  window.rkGoal = function (name, params) {
    if (metrikaOn && typeof window.ym === "function") window.ym(Number(metrikaId), "reachGoal", name, params);
  };

  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { /* хранилище недоступно — работаем без него */ }
    return null;
  }

  /* ---------- Список покупок (localStorage) ---------- */

  var LIST_KEY = "rk-list";
  window.rkList = {
    get: function () { var l = store(LIST_KEY); return Array.isArray(l) ? l : []; },
    set: function (items) { store(LIST_KEY, items.slice(0, 50)); updateBadge(); },
    add: function (item) { var l = this.get(); l.push(item); this.set(l); return l.length; }
  };
  function updateBadge() {
    var el = document.getElementById("list-count");
    if (!el) return;
    var n = window.rkList.get().length;
    el.textContent = String(n);
    el.hidden = !n;
    el.parentNode.setAttribute("aria-label", n ? "Список покупок: " + n : "Список покупок");
  }
  updateBadge();

  /* ---------- Светлая / тёмная тема ---------- */

  // Без выбора тема берётся из настройки системы; кнопка запоминает выбор (rk-theme).
  // Атрибут data-theme ставит ещё скрипт в <head>, до отрисовки страницы.
  var themeBtn = document.getElementById("theme-btn");
  var darkQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  function currentTheme() {
    var t = document.documentElement.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : (darkQuery && darkQuery.matches ? "dark" : "light");
  }
  function themeLabel() {
    if (!themeBtn) return;
    var dark = currentTheme() === "dark";
    themeBtn.setAttribute("aria-label", dark ? "Включить светлую тему" : "Включить тёмную тему");
    themeBtn.setAttribute("title", dark ? "Светлая тема" : "Тёмная тема");
  }
  if (themeBtn) {
    themeLabel();
    themeBtn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("rk-theme", next); } catch (e) { /* без хранилища — до перезагрузки */ }
      themeLabel();
    });
    if (darkQuery && darkQuery.addEventListener) darkQuery.addEventListener("change", themeLabel);
  }

  /* ---------- Уведомление о cookie ---------- */

  if (!store("rk-cookie-ok")) {
    var bar = document.createElement("div");
    bar.className = "cookie";
    bar.setAttribute("role", "region");
    bar.setAttribute("aria-label", "Уведомление о cookie");
    bar.innerHTML = '<p>Мы используем cookie и Яндекс Метрику для статистики. <a href="privacy.html">Подробнее</a></p>' +
      '<button type="button">Понятно</button>';
    // Не перекрываем прилипающую полосу с итогом на телефоне.
    var mbar = document.getElementById("mbar");
    var place = function () {
      bar.style.bottom = (mbar && mbar.offsetHeight ? mbar.offsetHeight : 0) + 8 + "px";
    };
    bar.querySelector("button").addEventListener("click", function () {
      store("rk-cookie-ok", 1);
      bar.remove();
      window.removeEventListener("resize", place);
    });
    document.body.appendChild(bar);
    place();
    window.addEventListener("resize", place);
  }

  // Клик по партнёрской ссылке — на калькуляторах и в статьях.
  document.addEventListener("click", function (e) {
    var link = e.target.closest && e.target.closest("a[data-aff]");
    if (!link) return;
    var form = document.querySelector("[data-calc]");
    var pageName = location.pathname.split("/").pop().replace(/\.html$/, "") || "index";
    window.rkGoal("affiliate_click", {
      calc: form ? form.getAttribute("data-calc") : pageName,
      item: link.getAttribute("data-aff"),
      shop: link.getAttribute("data-shop")
    });
  });

  /* ---------- Реклама РСЯ ---------- */

  var slots = document.querySelectorAll("[data-rsy]");
  if (slots.length && /^R-A-\d+-\d+$/.test(rsyBlockId)) {
    window.yaContextCb = window.yaContextCb || [];
    var s = document.createElement("script");
    s.src = "https://yandex.ru/ads/system/context.js";
    s.async = true;
    document.head.appendChild(s);
    Array.prototype.forEach.call(slots, function (slot, i) {
      slot.id = "yandex_rtb_" + rsyBlockId + (i ? "-" + i : "");
      slot.classList.add("ad-on");
      window.yaContextCb.push(function () {
        window.Ya.Context.AdvManager.render({ blockId: rsyBlockId, renderTo: slot.id });
      });
    });
  }
})();
