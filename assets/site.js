/* Общий код всех страниц: Яндекс Метрика и реклама РСЯ. */
(function () {
  "use strict";

  /* ===== НАСТРОЙКИ — замените заглушки ===== */
  var metrikaId = "METRIKA_ID";   // номер счётчика Метрики, например "98765432"
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
