/* Хабы «Ремонт под ключ»: этапы ремонта по размерам комнаты.
   Каждый этап считает assets/calc.js теми же формулами, что отдельный калькулятор,
   со значениями калькулятора по умолчанию (данные — в <script id="hub-data">). */
(function () {
  "use strict";

  window.RKHub = function (api) {
    var dataEl = document.getElementById("hub-data");
    if (!dataEl) return null;
    var data = JSON.parse(dataEl.textContent);
    var root = api.resultEl;
    var stageEls = root.querySelectorAll(".stage");
    var computed = [];   // по этапам: позиции для списка покупок
    var shown = [];      // разметка, чтобы не перерисовывать без изменений

    function opsString(ops) {
      return ops.map(function (o) { return o.kind + ":" + o.w + "x" + o.h + "x" + o.c; }).join(",");
    }

    // Значения калькулятора для позиции: его значения по умолчанию + размеры хаба + особенности этапа.
    function valuesFor(it) {
      var defs = data.defaults[it.calc];
      var v = {}, k;
      for (k in defs) v[k] = defs[k];
      ["room_l", "room_w", "room_h"].forEach(function (f) { if (f in defs) v[f] = api.val(f); });
      if (it.room === "apron") { v.room_l = api.val("apron_l"); v.room_w = api.val("apron_h"); }
      if (it.room === "ext") v.room_l = api.val("ext_l") || api.val("room_l");
      for (k in it.set) v[k] = it.set[k];
      return v;
    }

    function compute(it, allOps) {
      var v = valuesFor(it);
      var ops = it.ops === "all" ? allOps : it.ops === "w" ? allOps.filter(function (o) { return o.kind === "w"; }) : [];
      if (it.doors) {
        var doors = allOps.filter(function (o) { return o.kind === "d"; });
        v.doors = String(doors.reduce(function (s, o) { return s + o.c; }, 0));
        if (doors.length) v.door_w = String(doors[0].w);
      }
      var r = api.run(it.calc, v, ops);
      var q = new URLSearchParams(v);
      if (data.openings.indexOf(it.calc) >= 0) q.set("o", opsString(ops));
      // Ссылка на фартук или наружную стену — не размеры комнаты: калькулятор их не запоминает.
      if (v.room_l !== api.val("room_l") || ("room_w" in v && v.room_w !== api.val("room_w"))) q.set("mem", "0");
      var url = data.pages[it.calc] + "?" + q.toString();
      if (r.error) return { error: r.error, url: url };

      var findRow = function (label) {
        return r.rows.filter(function (row) { return row[0].indexOf(label) === 0; })[0];
      };
      var main, sub = "";
      if (it.row) {
        var row = findRow(it.row);
        if (!row) return null;
        // «≈ 136 кг (6 мешков по 25 кг)» → число отдельно, пояснение в скобках — подписью.
        var m = /^(.*?) \((.*)\)$/.exec(api.groupDigits(row[1]));
        main = m ? m[1] : api.groupDigits(row[1]);
        sub = m ? m[2] : "";
      } else {
        main = api.groupDigits(r.big.value + " " + r.big.unit);
        sub = r.sub ? api.groupDigits(r.sub) : "";
      }
      var extra = it.rows.map(findRow).filter(Boolean).map(function (row) { return [row[0], api.groupDigits(row[1])]; });
      return { main: main, sub: sub, rows: extra, url: url, entry: { name: it.name, qty: main, sub: sub, url: url, buy: it.buy } };
    }

    function itemHtml(it, res) {
      if (res.error) {
        return '<div class="si"><span class="si-name">' + api.esc(it.name) + '</span><p class="si-err">' + api.esc(res.error) + "</p></div>";
      }
      return '<div class="si"><span class="si-name">' + api.esc(it.name) + '</span><b class="si-val">' + api.esc(res.main) + "</b>" +
        (res.sub ? '<span class="si-sub">' + api.esc(res.sub) + "</span>" : "") +
        (res.rows.length ? '<ul class="si-rows">' + res.rows.map(function (row) {
          return "<li><span>" + api.esc(row[0]) + "</span><b>" + api.esc(row[1]) + "</b></li>";
        }).join("") + "</ul>" : "") +
        '<a class="si-link" href="' + api.esc(res.url) + '">Уточнить в калькуляторе →</a></div>';
    }

    function update(limitError) {
      var allOps = api.readOpenings();
      var ok = !limitError;
      data.stages.forEach(function (st, i) {
        var el = stageEls[i];
        var on = true;
        for (var k in st.when || {}) on = on && api.val(k) === st.when[k];
        el.hidden = !on;
        var html, entries = [];
        if (limitError) {
          html = '<p class="si-err">' + api.esc(limitError) + "</p>";
        } else {
          // Одинаковые ссылки подряд (клей и затирка из одного расчёта плитки) — одна кнопка «Уточнить».
          var lastUrl = "";
          html = st.items.map(function (it) {
            var res = compute(it, allOps);
            if (!res) return "";
            if (res.error) { if (on) ok = false; } else entries.push(res.entry);
            var out = itemHtml(it, res);
            if (res.url === lastUrl) out = out.replace(/<a class="si-link"[^>]*>[^<]*<\/a>/, "");
            lastUrl = res.url;
            return out;
          }).join("");
        }
        computed[i] = on ? entries.map(function (e) {
          return { name: e.name, qty: e.qty, sub: e.sub, calc: data.title + ": " + st.title, url: e.url, buy: e.buy };
        }) : [];
        if (shown[i] !== html) {
          shown[i] = html;
          el.querySelector(".stage-res").innerHTML = '<div class="si-grid">' + html + "</div>";
        }
        el.querySelector(".stage-add").disabled = !computed[i].length;
      });
      return ok;
    }

    function addEntries(list, btn, stageId) {
      if (!window.rkList || !list.length) return;
      var n = 0;
      list.forEach(function (e) { n = window.rkList.add(e); });
      api.flash(btn, "Добавлено ✓ В списке: " + n);
      api.goal("list_add", { calc: api.type, stage: stageId });
    }

    root.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-act]");
      if (!btn) return;
      var act = btn.getAttribute("data-act");
      if (act === "hub-stage") {
        var i = Number(btn.getAttribute("data-stage"));
        addEntries(computed[i] || [], btn, data.stages[i].id);
      }
      if (act === "hub-all") addEntries([].concat.apply([], computed), btn, "all");
    });

    return update;
  };
})();
