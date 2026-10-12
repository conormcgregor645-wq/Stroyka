/* Калькуляторы ремонта: плитка, обои, краска, ламинат. */
(function () {
  "use strict";

  var form = document.getElementById("calc-form");
  if (!form) return;
  var type = form.getAttribute("data-calc");
  var resultEl = document.getElementById("result");
  var ROOM_KEY = "rk-room";
  var ROOM_FIELDS = ["room_l", "room_w", "room_h"];

  /* ---------- helpers ---------- */

  function num(name, fallback) {
    var el = form.elements[name];
    if (!el) return fallback || 0;
    var v = parseFloat(String(el.value).replace(",", "."));
    return isFinite(v) && v >= 0 ? v : (fallback || 0);
  }
  function val(name) {
    var el = form.elements[name];
    return el ? el.value : "";
  }
  function fmt(n, digits) {
    return Number(n).toLocaleString("ru-RU", {
      minimumFractionDigits: 0,
      maximumFractionDigits: digits == null ? 2 : digits
    });
  }
  function money(n) {
    return fmt(Math.round(n), 0) + " ₽";
  }
  function plural(n, one, few, many) {
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
    return many;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function storageGet(key) {
    try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { return null; }
  }
  function storageSet(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* ignore */ }
  }

  /* ---------- openings (doors / windows) ---------- */

  var openingsEl = document.getElementById("openings");
  var addOpeningBtn = document.getElementById("add-opening");
  var openingSeq = 0;

  function addOpening(kind, w, h, count) {
    if (!openingsEl) return;
    openingSeq++;
    var id = "op" + openingSeq;
    var row = document.createElement("div");
    row.className = "opening";
    row.innerHTML =
      '<div class="field"><label for="' + id + 'k">Проём</label>' +
      '<select id="' + id + 'k" data-op="kind"><option value="d">Дверь</option><option value="w">Окно</option></select></div>' +
      '<div class="field"><label for="' + id + 'w">Ширина, м</label>' +
      '<input id="' + id + 'w" data-op="w" type="text" inputmode="decimal" value="' + w + '"></div>' +
      '<div class="field"><label for="' + id + 'h">Высота, м</label>' +
      '<input id="' + id + 'h" data-op="h" type="text" inputmode="decimal" value="' + h + '"></div>' +
      '<div class="field"><label for="' + id + 'c">Кол-во</label>' +
      '<input id="' + id + 'c" data-op="c" type="number" min="1" step="1" value="' + count + '"></div>' +
      '<button type="button" class="icon-btn" aria-label="Удалить проём" title="Удалить">×</button>';
    row.querySelector("select").value = kind;
    row.querySelector("button").addEventListener("click", function () {
      row.remove();
      update();
    });
    openingsEl.appendChild(row);
  }

  function readOpenings() {
    if (!openingsEl) return [];
    return Array.prototype.map.call(openingsEl.querySelectorAll(".opening"), function (row) {
      function f(k) {
        var v = parseFloat(String(row.querySelector('[data-op="' + k + '"]').value).replace(",", "."));
        return isFinite(v) && v > 0 ? v : 0;
      }
      return {
        kind: row.querySelector('[data-op="kind"]').value,
        w: f("w"),
        h: f("h"),
        c: Math.max(1, Math.round(f("c")) || 1)
      };
    });
  }
  function openingsArea(list) {
    return list.reduce(function (s, o) { return s + o.w * o.h * o.c; }, 0);
  }

  if (addOpeningBtn) {
    addOpeningBtn.addEventListener("click", function () {
      addOpening("w", "1.4", "1.5", 1);
      update();
    });
  }

  /* ---------- rendering ---------- */

  function shopHtml(items) {
    var partners = window.PARTNERS || [];
    if (!items || !items.length || !partners.length) return "";
    var html = '<div class="shop"><h3>Где купить</h3>';
    items.forEach(function (item) {
      html += '<div class="shop-item"><div class="name">' + esc(item.name) + '</div><div class="shop-links">';
      partners.forEach(function (p) {
        var url = p.search.replace("{q}", encodeURIComponent(item.q));
        var href = (p.wrap || "{url}").replace("{url}", encodeURIComponent(url));
        if (p.wrap === "{url}" || !p.wrap) href = url;
        html += '<a href="' + esc(href) + '" target="_blank" rel="sponsored nofollow noopener">' + esc(p.name) + "</a>";
      });
      html += "</div></div>";
    });
    html += '<p class="disclosure">Ссылки на магазины могут быть партнёрскими: при покупке сайт получает небольшую комиссию, цена для вас не меняется.</p></div>';
    return html;
  }

  var lastText = "";

  function render(r) {
    var html = "";
    if (r.error) {
      html = '<div class="big-label">Результат</div><p class="warn">' + esc(r.error) + "</p>";
      resultEl.innerHTML = html;
      lastText = "";
      return;
    }
    html += '<div class="big-label">' + esc(r.big.label) + "</div>";
    html += '<div class="big">' + esc(r.big.value) + " <small>" + esc(r.big.unit) + "</small></div>";
    html += '<ul class="res-list">';
    r.rows.forEach(function (row) {
      html += "<li><span>" + esc(row[0]) + "</span><b>" + esc(row[1]) + "</b></li>";
    });
    html += "</ul>";
    (r.warn || []).forEach(function (w) {
      html += '<p class="warn">' + esc(w) + "</p>";
    });
    html +=
      '<div class="actions">' +
      '<button type="button" data-act="copy">Скопировать расчёт</button>' +
      '<button type="button" data-act="link">Ссылка на расчёт</button>' +
      '<button type="button" data-act="print">Печать</button>' +
      "</div>";
    html += shopHtml(r.shop);
    resultEl.innerHTML = html;

    lastText =
      document.title.split("—")[0].trim() + "\n" +
      r.big.label + ": " + r.big.value + " " + r.big.unit + "\n" +
      r.rows.map(function (row) { return row[0] + ": " + row[1]; }).join("\n");
  }

  function flash(btn, text) {
    var old = btn.textContent;
    btn.textContent = text;
    setTimeout(function () { btn.textContent = old; }, 1500);
  }
  function copy(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn, "Скопировано ✓"); },
        function () { window.prompt("Скопируйте:", text); });
    } else {
      window.prompt("Скопируйте:", text);
    }
  }

  resultEl.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-act]");
    if (!btn) return;
    var act = btn.getAttribute("data-act");
    if (act === "copy") copy(lastText, btn);
    if (act === "link") copy(shareUrl(), btn);
    if (act === "print") window.print();
  });

  /* ---------- share via URL ---------- */

  function serialize() {
    var params = new URLSearchParams();
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name) return;
      if ((el.type === "radio" || el.type === "checkbox") && !el.checked) return;
      params.set(el.name, el.value);
    });
    var ops = readOpenings();
    if (openingsEl) {
      params.set("o", ops.map(function (o) { return o.kind + ":" + o.w + "x" + o.h + "x" + o.c; }).join(","));
    }
    return params;
  }
  function shareUrl() {
    return location.origin + location.pathname + "?" + serialize().toString();
  }
  function restore() {
    var params = new URLSearchParams(location.search);
    var fromUrl = Array.from(params.keys()).length > 0;
    if (fromUrl) {
      params.forEach(function (value, key) {
        var el = form.elements[key];
        if (!el) return;
        if (el.length && el[0] && el[0].type === "radio") {
          Array.prototype.forEach.call(el, function (r) { r.checked = r.value === value; });
        } else {
          el.value = value;
        }
      });
    } else {
      var room = storageGet(ROOM_KEY);
      if (room) {
        ROOM_FIELDS.forEach(function (k) {
          if (form.elements[k] && room[k]) form.elements[k].value = room[k];
        });
      }
    }
    if (!openingsEl) return;
    var o = params.get("o");
    if (fromUrl && o !== null) {
      o.split(",").filter(Boolean).forEach(function (part) {
        var m = part.match(/^([dw]):([\d.]+)x([\d.]+)x(\d+)$/);
        if (m) addOpening(m[1], m[2], m[3], m[4]);
      });
    } else {
      addOpening("d", "0.8", "2.0", 1);
      addOpening("w", "1.4", "1.5", 1);
    }
  }

  /* ---------- calculators ---------- */

  function room() {
    var L = num("room_l"), W = num("room_w"), H = num("room_h");
    return { L: L, W: W, H: H, floor: L * W, perimeter: 2 * (L + W) };
  }

  var calculators = {
    tile: function () {
      var r = room();
      var surface = val("surface");
      var ops = readOpenings();
      var wallArea = Math.max(0, r.perimeter * r.H - openingsArea(ops));
      var area = surface === "floor" ? r.floor : surface === "walls" ? wallArea : r.floor + wallArea;
      var a = num("tile_w"), b = num("tile_h");
      var joint = num("joint"), thick = num("thickness", 8);
      var reserve = num("reserve") / 100;
      var perPack = Math.round(num("per_pack"));
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!a || !b) return { error: "Введите размер плитки." };

      var tileM2 = (a / 100) * (b / 100);
      var count = Math.ceil((area / tileM2) * (1 + reserve));
      var buyM2 = count * tileM2;
      var packs = perPack > 0 ? Math.ceil(count / perPack) : 0;
      if (packs) { count = packs * perPack; buyM2 = count * tileM2; }

      var maxSide = Math.max(a, b);
      var gluePerM2 = maxSide <= 20 ? 3.5 : maxSide <= 40 ? 4.5 : 6;
      var glueKg = area * gluePerM2;
      var A = a * 10, B = b * 10; // мм
      var groutKg = joint > 0 ? ((A + B) / (A * B)) * thick * joint * 1.6 * area * 1.1 : 0;
      var crosses = Math.ceil(count * (joint > 0 ? 3 : 0) / 100) * 100;

      var rows = [
        ["Площадь облицовки", fmt(area) + " м²"],
        ["Площадь плитки к покупке", fmt(buyM2) + " м²"]
      ];
      if (packs) rows.push(["Упаковок", packs + " упак. по " + perPack + " шт."]);
      rows.push(["Плиточный клей", "≈ " + fmt(glueKg, 0) + " кг (" + Math.ceil(glueKg / 25) + " меш. по 25 кг)"]);
      if (groutKg) rows.push(["Затирка", "≈ " + fmt(groutKg, 1) + " кг (" + Math.ceil(groutKg / 2) + " уп. по 2 кг)"]);
      if (crosses) rows.push(["Крестики / СВП", "≈ " + fmt(crosses, 0) + " шт."]);
      if (price) rows.push(["Стоимость плитки", money(buyM2 * price)]);

      var warn = [];
      if (surface !== "floor" && !r.H) warn.push("Для стен укажите высоту помещения.");
      if (reserve < 0.05) warn.push("Запас меньше 5% — рискованно: плитка бьётся при подрезке, а докупить ту же партию (тон и калибр) бывает невозможно.");

      return {
        big: { label: "Нужно плитки", value: fmt(count, 0), unit: plural(count, "плитка", "плитки", "плиток") },
        rows: rows,
        warn: warn,
        shop: [
          { name: "Плитка " + fmt(a) + "×" + fmt(b) + " см", q: "керамическая плитка " + fmt(a) + "x" + fmt(b) },
          { name: "Плиточный клей", q: "плиточный клей 25 кг" },
          { name: "Затирка для швов", q: "затирка для плитки" }
        ]
      };
    },

    wallpaper: function () {
      var r = room();
      var ops = readOpenings();
      var rollW = num("roll_w"), rollL = num("roll_l");
      var rapport = num("rapport") / 100;
      var match = val("match");
      var price = num("price");
      if (!r.perimeter || !r.H) return { error: "Введите длину, ширину и высоту помещения." };
      if (!rollW || !rollL) return { error: "Введите размеры рулона." };

      var wallArea = Math.max(0, r.perimeter * r.H - openingsArea(ops));
      var effWidth = wallArea / r.H;
      var strips = Math.ceil(effWidth / rollW - 1e-9);
      var stripLen = r.H + 0.1; // припуск 5 см сверху и снизу
      if (rapport > 0 && match !== "none") {
        stripLen = Math.ceil(stripLen / rapport - 1e-9) * rapport;
        if (match === "offset") stripLen += rapport / 2;
      }
      var perRoll = Math.floor(rollL / stripLen + 1e-9);
      if (perRoll < 1) {
        return { error: "Полоса длиннее рулона (" + fmt(stripLen) + " м). Выберите рулон длиннее." };
      }
      var rolls = Math.ceil(strips / perRoll);
      var waste = rolls * rollL * rollW - wallArea;
      var glueM2 = rolls * rollL * rollW;

      var rows = [
        ["Площадь стен без проёмов", fmt(wallArea) + " м²"],
        ["Полос (полотен)", strips + " шт."],
        ["Длина полосы с припуском", fmt(stripLen) + " м"],
        ["Полос из одного рулона", perRoll + " шт."],
        ["Обойный клей", "≈ " + Math.ceil(glueM2 / 25) + " уп. (на ~25 м² каждая)"],
        ["Обрезки", "≈ " + fmt(Math.max(0, waste), 1) + " м²"]
      ];
      if (price) rows.push(["Стоимость обоев", money(rolls * price)]);

      return {
        big: { label: "Нужно обоев", value: fmt(rolls, 0), unit: plural(rolls, "рулон", "рулона", "рулонов") },
        rows: rows,
        warn: ["Купите на 1 рулон больше из той же партии — номер партии указан на этикетке, оттенок у разных партий отличается."],
        shop: [
          { name: "Обои " + (rollW >= 1 ? "метровые" : "0,53 м"), q: rollW >= 1 ? "обои флизелиновые 1,06" : "обои 0,53" },
          { name: "Обойный клей", q: "обойный клей" },
          { name: "Грунтовка", q: "грунтовка глубокого проникновения" }
        ]
      };
    },

    paint: function () {
      var r = room();
      var surface = val("surface");
      var ops = readOpenings();
      var wallArea = Math.max(0, r.perimeter * r.H - openingsArea(ops));
      var area = surface === "ceiling" ? r.floor : surface === "walls" ? wallArea : r.floor + wallArea;
      var layers = Math.max(1, Math.round(num("layers", 2)));
      var coverage = num("coverage");
      var can = num("can");
      var reserve = num("reserve") / 100;
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!coverage) return { error: "Введите расход краски (м² на литр)." };

      var liters = (area * layers / coverage) * (1 + reserve);
      var cans = can ? Math.ceil(liters / can - 1e-9) : 0;
      var primer = area * 0.1;

      var rows = [
        ["Площадь окраски", fmt(area) + " м²"],
        ["Слоёв", String(layers)],
        ["Краски с запасом", fmt(liters, 1) + " л"]
      ];
      if (cans) rows.push(["Тары по " + fmt(can) + " л", cans + " шт. (" + fmt(cans * can, 1) + " л)"]);
      rows.push(["Грунтовка (1 слой)", "≈ " + fmt(primer, 1) + " л"]);
      rows.push(["Малярный скотч", "≈ " + fmt(Math.ceil(r.perimeter * (surface === "walls" ? 2 : 1) + ops.reduce(function (s, o) { return s + 2 * (o.w + o.h) * o.c; }, 0)), 0) + " м"]);
      if (price && cans) rows.push(["Стоимость краски", money(cans * price)]);

      return {
        big: { label: "Нужно краски", value: fmt(liters, 1), unit: "л" },
        rows: rows,
        warn: coverage > 12 ? ["Расход больше 12 м²/л встречается редко — проверьте значение на банке."] : [],
        shop: [
          { name: surface === "ceiling" ? "Краска для потолка" : "Краска для стен", q: surface === "ceiling" ? "краска для потолка" : "краска для стен моющаяся" },
          { name: "Грунтовка", q: "грунтовка для стен под покраску" },
          { name: "Валики и кюветы", q: "набор малярный валик кювета" }
        ]
      };
    },

    laminate: function () {
      var r = room();
      var reserve = num("reserve") / 100;
      var pack = num("pack");
      var doors = Math.round(num("doors"));
      var doorW = num("door_w");
      var underlayRoll = num("underlay");
      var plinthLen = num("plinth");
      var price = num("price");
      if (!r.floor) return { error: "Введите длину и ширину комнаты." };
      if (!pack) return { error: "Введите площадь одной упаковки ламината." };

      var packs = Math.ceil((r.floor * (1 + reserve)) / pack - 1e-9);
      var buyM2 = packs * pack;
      var underlay = underlayRoll ? Math.ceil((r.floor * 1.05) / underlayRoll - 1e-9) : 0;
      var plinthM = Math.max(0, r.perimeter - doors * doorW);
      var plinths = plinthLen ? Math.ceil((plinthM * 1.05) / plinthLen - 1e-9) : 0;

      var rows = [
        ["Площадь пола", fmt(r.floor) + " м²"],
        ["Ламинат к покупке", fmt(buyM2) + " м²"],
        ["Остаток после укладки", "≈ " + fmt(Math.max(0, buyM2 - r.floor), 1) + " м²"]
      ];
      if (underlay) rows.push(["Подложка", underlay + " рул. по " + fmt(underlayRoll) + " м²"]);
      if (plinths) rows.push(["Плинтус", plinths + " шт. по " + fmt(plinthLen) + " м (" + fmt(plinthM, 1) + " м)"]);
      rows.push(["Углы плинтуса (внутр.)", "4 шт."]);
      if (doors) rows.push(["Заглушки плинтуса", doors * 2 + " шт."]);
      if (doors) rows.push(["Порожки", doors + " шт."]);
      if (price) rows.push(["Стоимость ламината", money(packs * price)]);

      return {
        big: { label: "Нужно ламината", value: fmt(packs, 0), unit: plural(packs, "упаковка", "упаковки", "упаковок") },
        rows: rows,
        warn: reserve < 0.05 ? ["Запас меньше 5% подходит только для идеально прямоугольной комнаты без подрезки."] : [],
        shop: [
          { name: "Ламинат", q: "ламинат 33 класс" },
          { name: "Подложка", q: "подложка под ламинат" },
          { name: "Плинтус", q: "плинтус напольный" }
        ]
      };
    }
  };

  /* ---------- wiring ---------- */

  function update() {
    var room = {};
    ROOM_FIELDS.forEach(function (k) {
      if (form.elements[k]) room[k] = form.elements[k].value;
    });
    var saved = storageGet(ROOM_KEY) || {};
    storageSet(ROOM_KEY, Object.assign(saved, room));

    var surface = val("surface");
    var openingsBlock = document.getElementById("openings-block");
    if (openingsBlock) openingsBlock.hidden = surface === "floor" || surface === "ceiling";

    render(calculators[type]());
  }

  restore();
  form.addEventListener("input", update);
  form.addEventListener("change", update);
  form.addEventListener("submit", function (e) { e.preventDefault(); update(); });
  update();
})();
