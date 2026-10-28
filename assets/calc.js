/* Калькуляторы ремонта: плитка, обои, краска, ламинат, штукатурка, шпаклёвка,
   гипсокартон, утеплитель, стяжка, кирпич. */
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
  // Округление вверх/вниз с допуском: 1,2 / 0,09 × 1,05 в JS даёт 14,000000000000002,
  // а нужно ровно 14 — без допуска калькулятор добавлял лишнюю штуку.
  function up(x) {
    return Math.ceil(x - 1e-7);
  }
  function down(x) {
    return Math.floor(x + 1e-7);
  }
  // Вверх до десятых: 8,336 л → 8,4 л (округление вниз оставило бы покупателя без краски).
  function up1(x) {
    return up(x * 10) / 10;
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
  function pcs(n) {
    return fmt(n, 0) + " шт.";
  }
  function bags(kg, bag) {
    var n = up(kg / bag);
    return n + " " + plural(n, "мешок", "мешка", "мешков") + " по " + fmt(bag) + " кг";
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
  function goal(name, params) {
    if (typeof window.rkGoal === "function") window.rkGoal(name, params);
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
    if (!openingsEl || openingsEl.closest("[hidden]")) return [];
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

  /* ---------- dependent fields: data-show="field:value1,value2" ---------- */

  function applyVisibility() {
    Array.prototype.forEach.call(form.querySelectorAll("[data-show]"), function (el) {
      var parts = el.getAttribute("data-show").split(":");
      el.hidden = parts[1].split(",").indexOf(val(parts[0])) < 0;
    });
  }

  /* ---------- rendering ---------- */

  var buyEl = document.getElementById("buy");
  var buyKey = "";

  function eridOf(url) {
    var m = /[?&]erid=([^&#]+)/.exec(url);
    return m ? decodeURIComponent(m[1]) : "";
  }

  // Блок «Купить …» под калькулятором: кнопка в магазин, маленькие кнопки и маркировка рекламы.
  function renderBuy(r) {
    if (!buyEl) return;
    var shop = window.SHOP || {};
    var cfg = (shop.pages || {})[type];
    var links = shop.links || {};
    var html = "";
    if (r && cfg && links[cfg.main]) {
      var used = [cfg.main];
      html = "<h2>" + esc(buyEl.getAttribute("data-title") || "Купить материал") + "</h2>" +
        '<p class="buy-lead">Нужно: ' + esc((r.big.value + " " + r.big.unit + (r.sub ? " · " + r.sub : "")).replace(/\.$/, "")) +
        ". Цены и доставка — на сайте магазина.</p>";
      html += '<div class="buy-actions">' + buyLink(links[cfg.main], cfg.main, shop.button, "buy-btn");
      var extra = (cfg.extra || []).filter(function (x) { return links[x[0]]; });
      if (extra.length) {
        html += '<div class="buy-extra">' + extra.map(function (x) {
          used.push(x[0]);
          return buyLink(links[x[0]], x[0], x[1], "buy-small");
        }).join("") + "</div>";
      }
      html += "</div>";
      // Маркировка рекламы: erid берём из каждой использованной ссылки.
      var erids = used.map(function (k) { return eridOf(links[k]); }).filter(function (e, i, all) { return e && all.indexOf(e) === i; });
      html += '<p class="ad-mark">Реклама. ' + esc(shop.advertiser) + ", ИНН " + esc(shop.inn) + ", erid: " + esc(erids.join(", ")) + "</p>";
    }
    // Перерисовываем только при изменении, чтобы не сбивать фокус и наведение.
    if (html !== buyKey) {
      buyKey = html;
      buyEl.innerHTML = html;
    }
  }

  function buyLink(url, key, text, cls) {
    return '<a class="' + cls + '" href="' + esc(url) + '" target="_blank" rel="sponsored nofollow noopener"' +
      ' data-aff="' + esc(key) + '" data-shop="' + esc((window.SHOP || {}).id || "") + '">' + esc(text) + "</a>";
  }

  var barBig = document.getElementById("mbar-big");
  var barSub = document.getElementById("mbar-sub");
  var lastText = "";

  function render(r) {
    var html = '<span class="res-cap">Нужно купить</span>';
    if (r.error) {
      resultEl.innerHTML = html + '<p class="res-error">' + esc(r.error) + "</p>";
      lastText = "";
      renderBuy(null);
      if (barBig) barBig.textContent = "—";
      if (barSub) barSub.textContent = "";
      return false;
    }
    var bigText = r.big.value + " " + r.big.unit;
    // Итог должен влезать в карточку одной строкой: чем длиннее текст, тем мельче шрифт.
    var n = bigText.length;
    var size = n <= 9 ? "" : n <= 11 ? " mid" : n <= 14 ? " long" : " xlong";
    html += '<div class="res-main"><span class="res-big' + size + '" data-value="' + esc(r.big.value) + '">' + esc(bigText) + "</span>";
    if (r.sub) html += '<span class="res-sub">' + esc(r.sub) + "</span>";
    html += '</div><ul class="res-rows">';
    r.rows.forEach(function (row) {
      html += "<li" + (row[0].indexOf("Стоимость") === 0 ? ' class="cost"' : "") + "><span>" + esc(row[0]) + "</span><b>" + esc(row[1]) + "</b></li>";
    });
    html += "</ul>";
    (r.warn || []).forEach(function (w) {
      html += '<p class="res-warn">' + esc(w) + "</p>";
    });
    html +=
      '<div class="res-actions">' +
      '<button type="button" class="share" data-act="share">Поделиться</button>' +
      '<button type="button" class="print" data-act="print">Распечатать</button>' +
      "</div>";
    resultEl.innerHTML = html;
    renderBuy(r);
    if (barBig) barBig.textContent = bigText;
    if (barSub) barSub.textContent = r.sub || "";

    lastText =
      document.title.split("—")[0].trim() + "\n" +
      r.big.label + ": " + bigText + (r.sub ? " (" + r.sub + ")" : "") + "\n" +
      r.rows.map(function (row) { return row[0] + ": " + row[1]; }).join("\n");
    return true;
  }

  function flash(btn, text) {
    var old = btn.textContent;
    btn.textContent = text;
    setTimeout(function () { btn.textContent = old; }, 1500);
  }
  function copy(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn, "Ссылка скопирована ✓"); },
        function () { window.prompt("Скопируйте:", text); });
    } else {
      window.prompt("Скопируйте:", text);
    }
  }
  // «Поделиться»: системное меню на телефоне, иначе — копируем ссылку со всеми параметрами.
  function share(btn) {
    var url = shareUrl();
    if (navigator.share) {
      navigator.share({ title: document.title, text: lastText, url: url }).catch(function () { /* отменено */ });
    } else {
      copy(url, btn);
    }
  }

  resultEl.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-act]");
    if (!btn) return;
    var act = btn.getAttribute("data-act");
    if (act === "share") share(btn);
    if (act === "print") window.print();
  });
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a[data-aff]");
    if (link) goal("affiliate_click", { calc: type, item: link.getAttribute("data-aff"), shop: link.getAttribute("data-shop") });
  });

  /* ---------- схема комнаты (SVG в масштабе) ---------- */

  var planEl = document.getElementById("plan");
  var planLabel = document.getElementById("plan-label");
  var BRICK_DEPTH = { "0.5": 0.12, "1": 0.25, "1.5": 0.38, "2": 0.51 };

  function drawPlan() {
    if (!planEl) return;
    var L = num("room_l"), W = num("room_w");
    var surface = val("surface"), mode = val("mode");
    var oneWall = type === "brick" && mode === "one";
    if (oneWall) W = BRICK_DEPTH[val("wall")] || 0.25; // одна стена: рисуем её толщину
    if (!(L > 0 && W > 0)) {
      planEl.innerHTML = '<text x="170" y="124" text-anchor="middle" class="svg-hint">Введите длину и ширину</text>';
      planEl.setAttribute("aria-label", "Схема появится после ввода размеров");
      if (planLabel) planLabel.textContent = "";
      return;
    }
    var walls = type === "wallpaper" || (type === "brick" && !oneWall) || (type === "drywall" && mode !== "ceiling") ||
      surface === "walls" || surface === "both";
    var floor = !(type === "wallpaper" || type === "brick" || (type === "drywall" && mode !== "ceiling") || surface === "walls");
    var s = Math.min(250 / L, 180 / W);
    var rw = Math.max(20, L * s), rh = Math.max(6, W * s);
    var x0 = (310 - rw) / 2 + 4, y0 = 34 + (186 - rh) / 2;
    var defs = "", fill = floor ? "pl-floor" : "pl-empty", label = fmt(L) + " × " + fmt(W) + " м", what = "План комнаты";

    if (type === "tile" && floor) {
      var tw = num("tile_w") / 100 * s, th = num("tile_h") / 100 * s;
      label = "плитка " + fmt(num("tile_w"), 1) + "×" + fmt(num("tile_h"), 1) + " см";
      what = "План пола с раскладкой плитки";
      if (tw >= 3 && th >= 3) {
        defs = '<pattern id="pl-pat" x="' + x0 + '" y="' + y0 + '" width="' + tw + '" height="' + th + '" patternUnits="userSpaceOnUse">' +
          '<rect class="pl-tile" width="' + tw + '" height="' + th + '"/></pattern>';
      }
    }
    if (type === "laminate") {
      var bl = num("board_l") / 1000 * s, bw = num("board_w") / 1000 * s;
      label = "доска " + Math.round(num("board_l")) + "×" + Math.round(num("board_w")) + " мм";
      what = "План пола с раскладкой ламината";
      if (bl >= 6 && bw >= 2) {
        // Ряды досок со смещением на полдоски.
        defs = '<pattern id="pl-pat" x="' + x0 + '" y="' + y0 + '" width="' + bl + '" height="' + 2 * bw + '" patternUnits="userSpaceOnUse">' +
          '<rect class="pl-floor" width="' + bl + '" height="' + 2 * bw + '"/>' +
          '<path class="pl-seam" d="M0 0V' + bw + "M0 " + bw + "H" + bl + "M" + bl / 2 + " " + bw + "V" + 2 * bw + "M0 " + 2 * bw + "H" + bl + '"/></pattern>';
      }
    }
    if (oneWall) { label = "стена " + fmt(L) + " м, толщина " + fmt(W * 1000, 0) + " мм"; what = "Стена в плане"; }

    var svg = defs ? "<defs>" + defs + "</defs>" : "";
    svg += '<rect class="' + fill + '" x="' + x0 + '" y="' + y0 + '" width="' + rw + '" height="' + rh + '"' + (defs ? ' style="fill:url(#pl-pat)"' : "") + "/>";
    if (walls) svg += '<rect class="pl-walls" x="' + x0 + '" y="' + y0 + '" width="' + rw + '" height="' + rh + '"/>';
    svg += '<rect class="pl-room" x="' + x0 + '" y="' + y0 + '" width="' + rw + '" height="' + rh + '"/>';
    // Размерные линии и подписи сторон.
    var x1 = x0 + rw, y1 = y0 + rh, cx = x0 + rw / 2, cy = y0 + rh / 2;
    svg += '<path class="pl-dim" d="M' + x0 + " 16H" + x1 + "M" + x0 + " 11V21M" + x1 + " 11V21M324 " + y0 + "V" + y1 + "M319 " + y0 + "H329M319 " + y1 + 'H329"/>';
    var lt = fmt(L) + " м", wt = oneWall ? fmt(W * 1000, 0) : fmt(W);
    svg += '<rect class="pl-box" x="' + (cx - 30) + '" y="7" width="60" height="18"/><text class="svg-num" x="' + cx + '" y="20" text-anchor="middle">' + esc(lt) + "</text>";
    svg += '<rect class="pl-box" x="305" y="' + (cy - 9) + '" width="35" height="18"/><text class="svg-num" x="322" y="' + (cy + 4) + '" text-anchor="middle">' + esc(wt) + "</text>";
    planEl.innerHTML = svg;
    planEl.setAttribute("aria-label", what + " " + fmt(L) + " на " + fmt(W) + " м");
    if (planLabel) planLabel.textContent = label;
  }

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

  // Площадь по переключателю surface: стены (без проёмов), пол/потолок или всё вместе.
  function surfaceArea(r, ops) {
    var walls = Math.max(0, r.perimeter * r.H - openingsArea(ops));
    var s = val("surface");
    if (s === "walls") return walls;
    if (s === "floor" || s === "ceiling") return r.floor;
    return walls + r.floor;
  }

  var calculators = {
    tile: function () {
      var r = room();
      var surface = val("surface");
      var ops = readOpenings();
      var area = surfaceArea(r, ops);
      var a = num("tile_w"), b = num("tile_h");
      var joint = num("joint"), thick = num("thickness", 8);
      var reserve = num("reserve") / 100;
      var perPack = Math.round(num("per_pack"));
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!a || !b) return { error: "Введите размер плитки." };

      var tileM2 = (a / 100) * (b / 100);
      var count = up((area / tileM2) * (1 + reserve));
      var packs = perPack > 0 ? up(count / perPack) : 0;
      var buyCount = packs ? packs * perPack : count;
      var buyM2 = buyCount * tileM2;

      var maxSide = Math.max(a, b);
      var gluePerM2 = maxSide <= 20 ? 3.5 : maxSide <= 40 ? 4.5 : 6;
      var glueKg = up(area * gluePerM2);
      var A = a * 10, B = b * 10; // мм
      var groutKg = joint > 0 ? up1(((A + B) / (A * B)) * thick * joint * 1.6 * area * 1.1) : 0;
      var crosses = joint > 0 ? up(count * 3 / 100) * 100 : 0;

      var rows = [
        ["Площадь облицовки", fmt(area) + " м²"],
        ["Площадь плитки к покупке", fmt(buyM2) + " м²"]
      ];
      if (packs) rows.push(["Упаковок", packs + " упак. по " + perPack + " шт. (" + buyCount + " шт.)"]);
      rows.push(["Плиточный клей", "≈ " + fmt(glueKg, 0) + " кг (" + bags(glueKg, 25) + ")"]);
      if (groutKg) rows.push(["Затирка", "≈ " + fmt(groutKg, 1) + " кг (" + up(groutKg / 2) + " уп. по 2 кг)"]);
      if (crosses) rows.push(["Крестики / СВП", "≈ " + pcs(crosses)]);
      if (price) rows.push(["Стоимость плитки", money(buyM2 * price)]);

      var warn = [];
      if (surface !== "floor" && !r.H) warn.push("Для стен укажите высоту помещения.");
      if (reserve < 0.05) warn.push("Запас меньше 5% — рискованно: плитка бьётся при подрезке, а докупить ту же партию (тон и калибр) бывает невозможно.");

      return {
        big: { label: "Нужно плитки", value: fmt(count, 0), unit: plural(count, "плитка", "плитки", "плиток") },
        sub: packs ? packs + " " + plural(packs, "упаковка", "упаковки", "упаковок") + " по " + perPack + " шт." : fmt(buyM2) + " м² плитки",
        rows: rows,
        warn: warn
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
      if (!wallArea) return { error: "Площадь проёмов больше площади стен — проверьте размеры окон и дверей." };
      var effWidth = wallArea / r.H;
      var strips = up(effWidth / rollW);
      var stripLen = r.H + 0.1; // припуск 5 см сверху и снизу
      if (rapport > 0 && match !== "none") {
        stripLen = up(stripLen / rapport) * rapport;
        if (match === "offset") stripLen += rapport / 2;
      }
      var perRoll = down(rollL / stripLen);
      if (perRoll < 1) {
        return { error: "Полоса длиннее рулона (" + fmt(stripLen) + " м). Выберите рулон длиннее." };
      }
      var rolls = up(strips / perRoll);
      var waste = rolls * rollL * rollW - wallArea;
      var glue = up(rolls * rollL * rollW / 25);

      var rows = [
        ["Площадь стен без проёмов", fmt(wallArea) + " м²"],
        ["Полос (полотен)", pcs(strips)],
        ["Длина полосы с припуском", fmt(stripLen) + " м"],
        ["Полос из одного рулона", pcs(perRoll)],
        ["Обойный клей", "≈ " + glue + " уп. (на ~25 м² каждая)"],
        ["Обрезки", "≈ " + fmt(Math.max(0, waste), 1) + " м²"]
      ];
      if (price) rows.push(["Стоимость обоев", money(rolls * price)]);

      var warn = ["Купите на 1 рулон больше из той же партии — номер партии указан на этикетке, оттенок у разных партий отличается."];
      if (rapport > 0 && match === "none") warn.unshift("Указан раппорт, но выбрано «Без подгонки» — раппорт не учтён. Если рисунок нужно совмещать, выберите тип подгонки.");

      return {
        big: { label: "Нужно обоев", value: fmt(rolls, 0), unit: plural(rolls, "рулон", "рулона", "рулонов") },
        sub: strips + " " + plural(strips, "полоса", "полосы", "полос") + " по " + fmt(stripLen) + " м · " + perRoll + " из рулона",
        rows: rows,
        warn: warn
      };
    },

    paint: function () {
      var r = room();
      var surface = val("surface");
      var ops = readOpenings();
      var area = surfaceArea(r, ops);
      var layers = Math.max(1, Math.round(num("layers", 2)));
      var coverage = num("coverage");
      var can = num("can");
      var reserve = num("reserve") / 100;
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!coverage) return { error: "Введите расход краски (м² на литр)." };

      var liters = up1((area * layers / coverage) * (1 + reserve));
      var cans = can ? up(liters / can) : 0;
      var primer = up1(area * 0.1);
      var tape = up(r.perimeter * (surface === "walls" ? 2 : 1) +
        ops.reduce(function (s, o) { return s + 2 * (o.w + o.h) * o.c; }, 0));

      var rows = [
        ["Площадь окраски", fmt(area) + " м²"],
        ["Слоёв", String(layers)],
        ["Краски с запасом", fmt(liters, 1) + " л"]
      ];
      if (cans) rows.push(["Тары по " + fmt(can) + " л", cans + " шт. (" + fmt(cans * can, 1) + " л)"]);
      rows.push(["Грунтовка (1 слой)", "≈ " + fmt(primer, 1) + " л"]);
      rows.push(["Малярный скотч", "≈ " + fmt(tape, 0) + " м"]);
      if (price && cans) rows.push(["Стоимость краски", money(cans * price)]);

      return {
        big: { label: "Нужно краски", value: fmt(liters, 1), unit: "л" },
        sub: cans ? cans + " " + plural(cans, "банка", "банки", "банок") + " по " + fmt(can) + " л" : "",
        rows: rows,
        warn: coverage > 12 ? ["Расход больше 12 м²/л встречается редко — проверьте значение на банке."] : []
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

      var packs = up((r.floor * (1 + reserve)) / pack);
      var buyM2 = packs * pack;
      var underlay = underlayRoll ? up((r.floor * 1.05) / underlayRoll) : 0;
      var plinthM = Math.max(0, r.perimeter - doors * doorW);
      var plinths = plinthLen ? up((plinthM * 1.05) / plinthLen) : 0;

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
        sub: fmt(buyM2) + " м² · запас " + fmt(reserve * 100, 0) + "%",
        rows: rows,
        warn: reserve < 0.05 ? ["Запас меньше 5% подходит только для идеально прямоугольной комнаты без подрезки."] : []
      };
    },

    plaster: function () {
      var r = room();
      var ops = readOpenings();
      var surface = val("surface");
      var area = surfaceArea(r, ops);
      var rate = num("mix");
      var thick = num("thickness");
      var bag = num("bag");
      var reserve = num("reserve") / 100;
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!thick) return { error: "Введите среднюю толщину слоя." };

      var kg = up1(area * thick * rate * (1 + reserve));
      var bagCount = up(kg / bag);
      // Маяки ставят через 1,5 м (правило 2 м должно опираться на два маяка).
      var beacons = 0;
      if (surface !== "ceiling") {
        var perWall = function (len) { return len ? up(len / 1.5) + 1 : 0; };
        beacons += 2 * (perWall(r.L) + perWall(r.W)) * up(r.H / 3);
      }
      if (surface !== "walls") beacons += (up(r.W / 1.5) + 1) * up(r.L / 3);
      var primer = up1(area * 0.15);

      var rows = [
        ["Площадь оштукатуривания", fmt(area) + " м²"],
        ["Расход смеси", fmt(rate * thick, 1) + " кг/м² при слое " + fmt(thick) + " мм"],
        ["Смеси с запасом", fmt(kg, 1) + " кг"],
        ["Маяки 3 м", "≈ " + pcs(beacons)],
        ["Грунтовка", "≈ " + fmt(primer, 1) + " л"]
      ];
      if (price) rows.push(["Стоимость смеси", money(bagCount * price)]);

      var warn = [];
      if (thick > 30) warn.push("Слой толще 30 мм наносят в несколько проходов, а свыше 50 мм — по армирующей сетке.");
      if (thick < 5) warn.push("Штукатурку тоньше 5 мм не наносят — для выравнивания мелких дефектов нужна шпаклёвка.");

      return {
        big: { label: "Нужно штукатурки", value: fmt(bagCount, 0), unit: plural(bagCount, "мешок", "мешка", "мешков") },
        sub: "по " + fmt(bag) + " кг · " + fmt(kg, 1) + " кг смеси",
        rows: rows,
        warn: warn
      };
    },

    putty: function () {
      var r = room();
      var ops = readOpenings();
      var area = surfaceArea(r, ops);
      var ts = num("start_mm"), rs = num("start_rate");
      var tf = num("finish_mm"), rf = num("finish_rate");
      var bs = num("start_bag"), bf = num("finish_bag");
      var reserve = num("reserve") / 100;
      if (!area) return { error: "Введите размеры помещения." };
      if (!(ts * rs) && !(tf * rf)) return { error: "Укажите толщину и расход хотя бы одного слоя." };
      if ((ts && !bs) || (tf && !bf)) return { error: "Укажите вес мешка." };

      var startKg = ts ? up1(area * ts * rs * (1 + reserve)) : 0;
      var finishKg = tf ? up1(area * tf * rf * (1 + reserve)) : 0;
      var total = Math.round((startKg + finishKg) * 10) / 10;
      var primer = up1(area * 0.1 * ((ts ? 1 : 0) + (tf ? 1 : 0)));
      var sandpaper = up(area / 10);

      var rows = [["Площадь шпаклевания", fmt(area) + " м²"]];
      if (startKg) rows.push(["Стартовая шпаклёвка", fmt(startKg, 1) + " кг (" + bags(startKg, bs) + ")"]);
      if (finishKg) rows.push(["Финишная шпаклёвка", fmt(finishKg, 1) + " кг (" + bags(finishKg, bf) + ")"]);
      rows.push(["Грунтовка (перед каждым слоем)", "≈ " + fmt(primer, 1) + " л"]);
      rows.push(["Абразивная сетка", "≈ " + sandpaper + " лист."]);

      var warn = [];
      if (ts > 5) warn.push("Стартовую шпаклёвку наносят слоем до 5 мм за проход. При больших перепадах дешевле сначала выровнять стены штукатуркой.");
      if (tf > 2) warn.push("Финишный слой обычно 0,5–1,5 мм. Проверьте толщину.");

      return {
        big: { label: "Нужно шпаклёвки", value: fmt(total, 1), unit: "кг" },
        sub: [startKg ? up(startKg / bs) + " меш. стартовой" : "", finishKg ? up(finishKg / bf) + " меш. финишной" : ""].filter(Boolean).join(" · "),
        rows: rows,
        warn: warn
      };
    },

    drywall: function () {
      var r = room();
      var ops = readOpenings();
      var mode = val("mode");
      var sheet = num("sheet");
      var layers = Math.max(1, Math.round(num("layers", 1)));
      var step = num("step");
      var plen = num("profile_len");
      var reserve = num("reserve") / 100;
      var price = num("price");
      var partL = num("part_l");
      if (!sheet || !step || !plen) return { error: "Заполните параметры листа и каркаса." };

      // Подвесы и крепления к основанию — с шагом не больше 1 м.
      function hangers(len) { return Math.max(1, up(len / 1) - 1); }
      var area, sides = 1, members, memberPieces, guideM, hang = 0, mainName, guideName;
      if (mode === "ceiling") {
        if (!r.floor) return { error: "Введите длину и ширину комнаты." };
        area = r.floor;
        members = Math.max(1, up(r.W / step) - 1);
        memberPieces = members * up(r.L / plen);
        guideM = r.perimeter;
        hang = members * hangers(r.L);
        mainName = "Профиль ПП 60×27";
        guideName = "Профиль ПН 28×27";
      } else if (mode === "partition") {
        if (!partL || !r.H) return { error: "Введите длину перегородки и высоту помещения." };
        area = Math.max(0, partL * r.H - openingsArea(ops));
        sides = 2;
        members = up(partL / step) + 1;
        memberPieces = members * up(r.H / plen);
        guideM = 2 * partL;
        mainName = "Профиль ПС 50×50";
        guideName = "Профиль ПН 50×40";
      } else {
        if (!r.perimeter || !r.H) return { error: "Введите размеры помещения." };
        area = Math.max(0, r.perimeter * r.H - openingsArea(ops));
        members = 2 * (up(r.L / step) + 1) + 2 * (up(r.W / step) + 1);
        memberPieces = members * up(r.H / plen);
        guideM = 2 * r.perimeter;
        hang = members * hangers(r.H);
        mainName = "Профиль ПП 60×27";
        guideName = "Профиль ПН 28×27";
      }
      if (!area) return { error: "Площадь проёмов больше площади обшивки — проверьте размеры." };

      var cladding = area * sides;
      var sheets = up(cladding * layers * (1 + reserve) / sheet);
      var guidePieces = up(guideM / plen);
      var screwRate = mode === "ceiling" ? 25 : 20;
      var screws = up(cladding * layers * screwRate);
      var bugs = hang * 2 + members * 4;
      var dowels = up(guideM / 0.5) + hang * 2;
      var tape = up(cladding * 1.2);
      var filler = up1(cladding * 0.35);

      var rows = [
        ["Площадь обшивки", fmt(cladding) + " м²" + (sides === 2 ? " (2 стороны)" : "")],
        [mainName, members + " " + (mode === "ceiling" ? plural(members, "линия", "линии", "линий") : plural(members, "стойка", "стойки", "стоек")) +
          " → " + pcs(memberPieces) + " по " + fmt(plen) + " м"],
        [guideName, fmt(guideM, 1) + " м → " + pcs(guidePieces)]
      ];
      if (hang) rows.push(["Прямые подвесы", pcs(hang)]);
      rows.push(["Саморезы по ГКЛ 3,5×25", "≈ " + pcs(screws)]);
      rows.push(["Саморезы-клопы 3,5×9,5", "≈ " + pcs(bugs)]);
      rows.push(["Дюбель-гвозди 6×40", "≈ " + pcs(dowels)]);
      rows.push(["Серпянка", "≈ " + tape + " м"]);
      rows.push(["Шпаклёвка для швов", "≈ " + fmt(filler, 1) + " кг"]);
      if (price) rows.push(["Стоимость листов", money(sheets * price)]);

      var warn = [];
      if (layers === 2) warn.push("Для второго слоя нужны саморезы длиной 35 мм.");
      if (mode === "partition" && ops.some(function (o) { return o.kind === "d"; })) {
        warn.push("Дверной проём в перегородке усиливают: добавьте по 2 стойки ПС на каждую дверь, лучше с деревянным бруском внутри.");
      }

      return {
        big: { label: "Нужно гипсокартона", value: fmt(sheets, 0), unit: plural(sheets, "лист", "листа", "листов") },
        sub: fmt(cladding) + " м² обшивки · " + (memberPieces + guidePieces) + " шт. профиля",
        rows: rows,
        warn: warn
      };
    },

    insulation: function () {
      var r = room();
      var ops = readOpenings();
      var surface = val("surface");
      var area = surfaceArea(r, ops);
      var total = num("total_mm");
      var bl = num("board_l"), bw = num("board_w"), bt = num("board_t");
      var perPack = Math.round(num("per_pack"));
      var reserve = num("reserve") / 100;
      var price = num("price");
      if (!area) return { error: "Введите размеры помещения." };
      if (!total || !bl || !bw || !bt) return { error: "Заполните толщину утепления и размеры плиты." };

      var layers = up(total / bt);
      var boardM2 = (bl / 1000) * (bw / 1000);
      var boards = up(area * layers * (1 + reserve) / boardM2);
      var packs = perPack ? up(boards / perPack) : 0;
      var volume = area * layers * bt / 1000;
      var film = up(area * 1.1);
      var dowels = surface === "walls" ? up(area * 6) : 0;

      var rows = [
        ["Площадь утепления", fmt(area) + " м²"],
        ["Слоёв по " + fmt(bt) + " мм", String(layers)],
        ["Плит " + fmt(bl) + "×" + fmt(bw) + " мм", pcs(boards)],
        ["Объём утеплителя", fmt(volume, 2) + " м³"],
        ["Пароизоляция (нахлёст 10 см)", "≈ " + film + " м²"]
      ];
      if (dowels) rows.push(["Дюбели-грибки", "≈ " + pcs(dowels)]);
      if (price && packs) rows.push(["Стоимость утеплителя", money(packs * price)]);

      var warn = [];
      if (layers * bt > total + 1e-7) warn.push("Толщина утепления не делится на толщину плиты — получится " + fmt(layers * bt) + " мм вместо " + fmt(total) + " мм.");
      if (layers > 1) warn.push("Второй слой кладут со смещением швов, чтобы не было мостиков холода.");

      return {
        big: packs
          ? { label: "Нужно утеплителя", value: fmt(packs, 0), unit: plural(packs, "упаковка", "упаковки", "упаковок") }
          : { label: "Нужно утеплителя", value: fmt(boards, 0), unit: plural(boards, "плита", "плиты", "плит") },
        sub: (packs ? "по " + perPack + " плит · " : "") + fmt(volume, 2) + " м³",
        rows: rows,
        warn: warn
      };
    },

    screed: function () {
      var r = room();
      var thick = num("thickness");
      var mix = val("mix");
      var reserve = num("reserve") / 100;
      if (!r.floor) return { error: "Введите длину и ширину комнаты." };
      if (!thick) return { error: "Введите среднюю толщину стяжки." };

      var volume = r.floor * thick / 1000;
      var rows = [
        ["Площадь пола", fmt(r.floor) + " м²"],
        ["Объём раствора", fmt(up1(volume * 100) / 100, 2) + " м³"]
      ];
      var warn = [];
      var big, sub;
      if (mix === "diy") {
        // Объём сухих компонентов на 1 м³ раствора — 1,3 м³ (песок и цемент уплотняются при затворении).
        var parts = num("ratio", 3);
        var v = volume * (1 + reserve);
        var cementKg = up(v * 1.3 / (1 + parts) * 1300);
        var sandM3 = up(v * 1.3 * parts / (1 + parts) * 100) / 100;
        var cementBags = up(cementKg / 50);
        rows.push(["Цемент М500", fmt(cementKg, 0) + " кг (" + bags(cementKg, 50) + ")"]);
        rows.push(["Песок", fmt(sandM3, 2) + " м³ (≈ " + fmt(up1(sandM3 * 1.5), 1) + " т)"]);
        rows.push(["Фиброволокно", "≈ " + fmt(up1(v * 0.9), 1) + " кг"]);
        big = { label: "Нужно цемента", value: fmt(cementBags, 0), unit: plural(cementBags, "мешок", "мешка", "мешков") };
        sub = "цемента по 50 кг · " + fmt(sandM3, 2) + " м³ песка";
        if (thick < 30) warn.push("Цементно-песчаную стяжку делают толщиной от 30 мм, на разделительном слое или утеплителе — от 40 мм.");
      } else {
        var rate = num("rate");
        var bag = num("bag");
        if (!rate || !bag) return { error: "Выберите смесь и вес мешка." };
        var kg = up1(r.floor * thick * rate * (1 + reserve));
        var bagCount = up(kg / bag);
        var price = num("price");
        rows.push(["Расход смеси", fmt(rate * thick, 1) + " кг/м²"]);
        rows.push(["Смеси с запасом", fmt(kg, 1) + " кг"]);
        if (price) rows.push(["Стоимость смеси", money(bagCount * price)]);
        big = { label: "Нужно смеси", value: fmt(bagCount, 0), unit: plural(bagCount, "мешок", "мешка", "мешков") };
        sub = "по " + fmt(bag) + " кг · " + fmt(kg, 1) + " кг смеси";
        if (rate >= 1.8 && thick < 30) warn.push("Цементно-песчаную стяжку делают толщиной от 30 мм. Для тонкого выравнивания выберите наливной пол.");
        if (rate < 1.8 && thick > 100) warn.push("Наливной пол заливают обычно слоем до 100 мм — проверьте инструкцию смеси.");
      }
      rows.push(["Демпферная лента", "≈ " + fmt(up(r.perimeter * 1.05), 0) + " м"]);
      if (mix === "diy") rows.push(["Армирующая сетка", "≈ " + up(r.floor * 1.1) + " м²"]);

      return { big: big, sub: sub, rows: rows, warn: warn };
    },

    brick: function () {
      var r = room();
      var ops = readOpenings();
      var mode = val("mode");
      var h = num("brick") / 1000;
      var k = num("wall"); // толщина стены в кирпичах: 0,5; 1; 1,5; 2
      var j = num("joint") / 1000;
      var reserve = num("reserve") / 100;
      var price = num("price");
      var len = mode === "one" ? r.L : r.perimeter;
      if (!len || !r.H) return { error: "Введите длину стен и высоту." };
      if (!h || !k) return { error: "Выберите кирпич и толщину стены." };

      var area = Math.max(0, len * r.H - openingsArea(ops));
      if (!area) return { error: "Площадь проёмов больше площади стен — проверьте размеры." };
      var DEPTH = { "0.5": 0.12, "1": 0.25, "1.5": 0.38, "2": 0.51 };
      var depth = DEPTH[String(k)] || k * 0.25;
      // На 1 м² лицевой поверхности в полкирпича: 1 / ((0,25 + шов) × (высота + шов)).
      var perM2 = 2 * k / ((0.25 + j) * (h + j));
      var net = area * perM2;
      var bricks = up(net * (1 + reserve));
      var mortar = Math.max(0, area * depth - net * 0.25 * 0.12 * h) * (1 + reserve);
      var mortarM3 = up(mortar * 100) / 100;
      var cementKg = up(mortar * 1.3 / 5 * 1300);
      var sandM3 = up(mortar * 1.3 * 4 / 5 * 100) / 100;

      var rows = [
        ["Площадь кладки без проёмов", fmt(area) + " м²"],
        ["Кирпичей на 1 м²", fmt(perM2, 1) + " шт."],
        ["Объём кладки", fmt(area * depth, 2) + " м³"],
        ["Раствор", "≈ " + fmt(mortarM3, 2) + " м³"],
        ["Цемент М500 (раствор 1:4)", "≈ " + fmt(cementKg, 0) + " кг (" + bags(cementKg, 50) + ")"],
        ["Песок", "≈ " + fmt(sandM3, 2) + " м³"]
      ];
      if (price) rows.push(["Стоимость кирпича", money(bricks * price)]);

      return {
        big: { label: "Нужно кирпича", value: fmt(bricks, 0), unit: plural(bricks, "кирпич", "кирпича", "кирпичей") },
        sub: fmt(mortarM3, 2) + " м³ раствора",
        rows: rows,
        warn: reserve < 0.05 ? ["Запас меньше 5% — кирпич бьётся при перевозке и подрезке."] : []
      };
    }
  };

  /* ---------- wiring ---------- */

  var touched = false;
  var goalSent = false;

  function update() {
    var room = {};
    ROOM_FIELDS.forEach(function (k) {
      if (form.elements[k]) room[k] = form.elements[k].value;
    });
    var saved = storageGet(ROOM_KEY) || {};
    storageSet(ROOM_KEY, Object.assign(saved, room));

    applyVisibility();
    var ok = render(calculators[type]());
    drawPlan();
    // Цель «расчёт выполнен» — один раз за визит и только после действий пользователя.
    if (ok && touched && !goalSent) {
      goalSent = true;
      goal("calc_done", { calc: type });
    }
  }

  restore();
  form.addEventListener("input", function () { touched = true; update(); });
  form.addEventListener("change", function () { touched = true; update(); });
  form.addEventListener("submit", function (e) { e.preventDefault(); update(); });
  update();
})();
