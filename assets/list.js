/* Список покупок (spisok.html): позиции из localStorage или из ссылки ?l=… */
(function () {
  "use strict";

  var root = document.getElementById("list-root");
  if (!root || !window.rkList) return;
  var shop = window.SHOP || {};
  var links = shop.links || {};

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  // Ссылка на расчёт — только на страницы самого сайта (список могут прислать по ссылке).
  function safeUrl(u) {
    return /^[a-z0-9-]+\.html(\?[^"'<>\s]*)?$/.test(String(u || "")) ? u : "";
  }

  /* ---------- список в адресе: base64url от JSON ---------- */

  var FIELDS = ["name", "qty", "sub", "calc", "url", "buy"];
  function encode(items) {
    var json = JSON.stringify(items.map(function (it) { return FIELDS.map(function (f) { return it[f] || ""; }); }));
    return btoa(unescape(encodeURIComponent(json))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function decode(str) {
    try {
      var json = decodeURIComponent(escape(atob(str.replace(/-/g, "+").replace(/_/g, "/"))));
      var rows = JSON.parse(json);
      if (!Array.isArray(rows)) return null;
      return rows.slice(0, 50).map(function (r) {
        var it = {};
        FIELDS.forEach(function (f, i) { it[f] = String((r || [])[i] || "").slice(0, 300); });
        return it;
      });
    } catch (e) {
      return null;
    }
  }

  var shared = decode(new URLSearchParams(location.search).get("l") || "");

  function items() {
    return shared || window.rkList.get();
  }

  function render() {
    var list = items();
    var html = "";
    if (shared) {
      html += '<div class="list-shared"><p>Это список по ссылке. Его можно сохранить в свой список в этом браузере.</p>' +
        '<button type="button" class="btn-primary" data-act="save">Сохранить в мой список</button></div>';
    }
    if (!list.length) {
      root.innerHTML = html + '<p class="list-empty">Список пуст. Откройте <a href="index.html#calc">калькулятор</a>, посчитайте материал и нажмите «Добавить в список покупок».</p>';
      return;
    }
    var erids = [];
    html += '<ul class="list-items">';
    list.forEach(function (it, i) {
      var url = safeUrl(it.url), buy = links[it.buy];
      html += '<li class="list-item"><div class="list-info"><b class="list-name">' + esc(it.name) + '</b>' +
        '<span class="list-qty">' + esc(it.qty) + "</span>" +
        (it.sub ? '<span class="list-sub">' + esc(it.sub) + "</span>" : "") +
        (it.calc ? '<span class="list-from">' + (url ? '<a href="' + esc(url) + '">' + esc(it.calc) + "</a>" : esc(it.calc)) + "</span>" : "") +
        '</div><div class="list-btns">';
      if (buy) {
        html += '<a class="buy-btn" href="' + esc(buy) + '" target="_blank" rel="sponsored nofollow noopener" data-aff="' + esc(it.buy) +
          '" data-shop="' + esc(shop.id || "") + '">' + esc(shop.button || "Купить") + "</a>";
        var m = /[?&]erid=([^&#]+)/.exec(buy);
        if (m && erids.indexOf(m[1]) < 0) erids.push(m[1]);
      }
      if (!shared) html += '<button type="button" class="icon-btn" data-act="remove" data-i="' + i + '" aria-label="Удалить «' + esc(it.name) + '»">×</button>';
      html += "</div></li>";
    });
    html += "</ul>";
    if (erids.length) {
      html += '<p class="ad-mark">Реклама. ' + esc(shop.advertiser) + ", ИНН " + esc(shop.inn) + ", erid: " + esc(erids.join(", ")) + "</p>";
    }
    html += '<div class="list-actions">' +
      '<button type="button" class="btn-primary" data-act="share">Поделиться ссылкой</button>' +
      '<button type="button" class="list-btn" data-act="print">Распечатать</button>' +
      (shared ? "" : '<button type="button" class="list-btn" data-act="clear">Очистить</button>') + "</div>";
    root.innerHTML = html;
  }

  function flash(btn, text) {
    var old = btn.textContent;
    btn.textContent = text;
    setTimeout(function () { btn.textContent = old; }, 1500);
  }

  root.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-act]");
    if (!btn) return;
    var act = btn.getAttribute("data-act");
    if (act === "remove") {
      var l = window.rkList.get();
      l.splice(Number(btn.getAttribute("data-i")), 1);
      window.rkList.set(l);
      render();
    }
    if (act === "clear" && window.confirm("Очистить список покупок?")) {
      window.rkList.set([]);
      render();
    }
    if (act === "print") window.print();
    if (act === "save") {
      window.rkList.set(window.rkList.get().concat(shared));
      shared = null;
      history.replaceState(null, "", location.pathname);
      render();
    }
    if (act === "share") {
      var url = location.origin + location.pathname + "?l=" + encode(items());
      if (navigator.share) {
        navigator.share({ title: "Список покупок — Метраж", url: url }).catch(function () { /* отменено */ });
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () { flash(btn, "Ссылка скопирована ✓"); },
          function () { window.prompt("Скопируйте ссылку:", url); });
      } else {
        window.prompt("Скопируйте ссылку:", url);
      }
    }
  });

  render();
})();
