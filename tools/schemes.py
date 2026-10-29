"""Схемы для страниц «Метража»: инлайн-SVG в стиле сайта.

Цвета задаются классами .sc-* в assets/style.css (через CSS-переменные),
поэтому схемы совпадают с оформлением страниц. Каждая схема — <figure> с
role="img", aria-label и подписью; ширина по экрану, отрисовка отложена
через content-visibility (см. .scheme в style.css).
"""
import math


def figure(svg, label, caption, view_box):
    return (f'<figure class="scheme"><svg viewBox="{view_box}" role="img" aria-label="{label}" '
            f'preserveAspectRatio="xMidYMid meet">{svg}</svg><figcaption>{caption}</figcaption></figure>')


def pair(items, legend=""):
    """Две мини-схемы рядом: [(svg, label, подпись, viewBox), ...]."""
    cells = "".join(
        f'<div class="scheme-cell"><svg viewBox="{vb}" role="img" aria-label="{label}">{svg}</svg>'
        f'<p class="scheme-sub">{sub}</p></div>' for svg, label, sub, vb in items)
    return f'<figure class="scheme scheme-pair">{cells}{legend}</figure>'


def dim_h(x1, x2, y, text):
    """Горизонтальная размерная линия с подписью по центру."""
    cx = (x1 + x2) / 2
    w = len(text) * 9 + 16
    return (f'<path class="sc-dim" d="M{x1} {y}H{x2}M{x1} {y - 6}V{y + 6}M{x2} {y - 6}V{y + 6}"/>'
            f'<rect class="sc-bg" x="{cx - w / 2}" y="{y - 11}" width="{w}" height="22"/>'
            f'<text class="sc-t" x="{cx}" y="{y + 6}" text-anchor="middle">{text}</text>')


def dim_v(x, y1, y2, text):
    cy = (y1 + y2) / 2
    return (f'<path class="sc-dim" d="M{x} {y1}V{y2}M{x - 6} {y1}H{x + 6}M{x - 6} {y2}H{x + 6}"/>'
            f'<text class="sc-t" x="{x}" y="{cy}" text-anchor="middle" transform="rotate(-90 {x} {cy})" dy="-8">{text}</text>')


def callout(x1, y1, x2, y2, text, anchor="start"):
    """Выноска: линия от объекта к подписи. text — строка или список строк."""
    lines = [text] if isinstance(text, str) else text
    tx = x2 + (6 if anchor == "start" else -6)
    spans = "".join(f'<tspan x="{tx}" dy="{0 if i == 0 else 19}">{t}</tspan>' for i, t in enumerate(lines))
    return (f'<path class="sc-lead" d="M{x1} {y1}L{x2} {y2}"/><circle class="sc-dot" cx="{x1}" cy="{y1}" r="3"/>'
            f'<text class="sc-t" x="{tx}" y="{y2 + 5}" text-anchor="{anchor}">{spans}</text>')


# ---------- плитка: как измерить ванную ----------

def bath_measure():
    x0, y0, w, h = 56, 50, 230, 180
    svg = f'<rect class="sc-floor" x="{x0}" y="{y0}" width="{w}" height="{h}"/>'
    # ванна вдоль верхней стены, короб в правом верхнем углу
    svg += f'<rect class="sc-bath" x="{x0 + 8}" y="{y0 + 8}" width="140" height="58" rx="24"/>'
    svg += f'<text class="sc-t" x="{x0 + 78}" y="{y0 + 43}" text-anchor="middle">ванна</text>'
    svg += (f'<pattern id="sc-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<path class="sc-hatch" d="M0 0V8"/></pattern>'
            f'<rect class="sc-boxfill" x="{x0 + w - 40}" y="{y0}" width="40" height="40"/>'
            f'<rect class="sc-box" x="{x0 + w - 40}" y="{y0}" width="40" height="40" fill="url(#sc-hatch)"/>')
    # стены с проёмом двери в нижней стене
    dx = x0 + w - 96
    svg += (f'<path class="sc-wall" d="M{dx} {y0 + h}H{x0}V{y0}H{x0 + w}V{y0 + h}H{dx + 60}"/>'
            f'<path class="sc-door" d="M{dx + 60} {y0 + h}L{dx + 60} {y0 + h - 60}"/>'
            f'<path class="sc-arc" d="M{dx} {y0 + h}A60 60 0 0 1 {dx + 60} {y0 + h - 60}"/>')
    svg += dim_h(x0, x0 + w, 22, "длина")
    svg += dim_v(26, y0, y0 + h, "ширина")
    svg += callout(x0 + w - 20, y0 + 20, 306, 40, "короб")
    svg += callout(x0 + 110, y0 + 125, 306, 118, ["пол:", "длина × ширина"])
    svg += callout(dx + 30, y0 + h, 306, 214, ["дверь:", "ширина × высота"])
    return figure(svg, "План ванной: длина и ширина комнаты, дверь, ванна и короб для труб",
                  "Измерьте длину и ширину у пола и на высоте 1,5 м, дверной проём, ванну и короб. "
                  "Дверь и закрытую ванной стену вычитают, грани короба — прибавляют.",
                  "0 0 460 250")


# ---------- плитка: прямая и диагональная раскладка ----------

def tile_layouts():
    size, t = 200, 46            # комната и плитка в пикселях
    # прямая: 4 целые плитки + подрезанный ряд
    straight = f'<rect class="sc-floor" x="10" y="10" width="{size}" height="{size}"/>'
    for i in range(5):
        for j in range(5):
            x, y = 10 + i * t, 10 + j * t
            cw, ch = min(t, 10 + size - x), min(t, 10 + size - y)
            cut = cw < t or ch < t
            straight += f'<rect class="{"sc-cut" if cut else "sc-tile"}" x="{x}" y="{y}" width="{cw}" height="{ch}"/>'
    straight += f'<rect class="sc-room" x="10" y="10" width="{size}" height="{size}"/>'
    # диагональ: ромбы, у стен — половинки (подрезка)
    d = size / 5
    diag = (f'<clipPath id="sc-clip"><rect x="10" y="10" width="{size}" height="{size}"/></clipPath>'
            f'<rect class="sc-floor" x="10" y="10" width="{size}" height="{size}"/><g clip-path="url(#sc-clip)">')
    centers = [(i * d, j * d) for i in range(6) for j in range(6)] + \
              [((i + .5) * d, (j + .5) * d) for i in range(5) for j in range(5)]
    for cx, cy in centers:
        edge = cx < 1 or cy < 1 or cx > size - 1 or cy > size - 1
        x, y, r = 10 + cx, 10 + cy, d / 2
        diag += f'<path class="{"sc-cut" if edge else "sc-tile"}" d="M{x} {y - r}L{x + r} {y}L{x} {y + r}L{x - r} {y}Z"/>'
    diag += f'</g><rect class="sc-room" x="10" y="10" width="{size}" height="{size}"/>'
    vb = f"0 0 {size + 20} {size + 20}"
    return pair([
        (straight, "Прямая раскладка: подрезка только в крайнем ряду у двух стен", "<b>Прямая</b> — подрезка в крайних рядах, запас 10%", vb),
        (diag, "Диагональная раскладка: подрезанные треугольники вдоль всех стен", "<b>Диагональная</b> — подрезка у всех стен, запас 15%", vb),
    ], '<p class="scheme-legend"><span class="sw sw-cut"></span>подрезанная плитка</p>')


# ---------- обои: раппорт ----------

def wallpaper_rapport():
    def strips(x0, shifts):
        out = ""
        for k, sh in enumerate(shifts):
            x = x0 + k * 44
            out += f'<rect class="sc-strip" x="{x}" y="40" width="40" height="240"/>'
            for m in range(-1, 4):
                cy = 40 + sh + m * 80 + 40
                if 50 < cy < 270:
                    out += f'<path class="sc-motif" d="M{x + 20} {cy - 10}L{x + 30} {cy}L{x + 20} {cy + 10}L{x + 10} {cy}Z"/>'
        return out
    svg = strips(66, [0, 0, 0]) + strips(270, [0, 40, 0])
    svg += '<path class="sc-match" d="M66 120H194M270 120H310M314 160H354M358 120H398"/>'
    svg += dim_v(46, 80, 160, "раппорт")
    svg += '<text class="sc-h" x="130" y="24" text-anchor="middle">прямая подгонка</text>'
    svg += '<text class="sc-h" x="334" y="24" text-anchor="middle">со смещением</text>'
    svg += callout(334, 160, 404, 210, ["сдвиг", "½"])
    return figure(svg, "Раппорт обоев: при прямой подгонке рисунок соседних полос на одной высоте, при подгонке со смещением сдвинут на половину раппорта",
                  "Раппорт — шаг, через который повторяется рисунок. При прямой подгонке узор соседних полос на одной высоте, "
                  "со смещением — каждая вторая полоса сдвинута на полраппорта, поэтому полосы получаются длиннее.",
                  "0 0 460 300")


# ---------- ламинат: смещение рядов ----------

def laminate_rows():
    x0, y0, w, rows, bh, bl = 30, 30, 410, 6, 30, 160
    shifts = [0, 72, 32, 112, 56, 136]
    svg = (f'<clipPath id="sc-lclip"><rect x="{x0 + 8}" y="{y0}" width="{w - 8}" height="{rows * bh}"/></clipPath>'
           f'<rect class="sc-floor" x="{x0 + 8}" y="{y0}" width="{w - 8}" height="{rows * bh}"/><g clip-path="url(#sc-lclip)">')
    for r, sh in enumerate(shifts):
        y = y0 + r * bh
        x = x0 + 8 - sh
        while x < x0 + w:
            svg += f'<rect class="sc-board" x="{x}" y="{y}" width="{bl}" height="{bh}"/>'
            x += bl
    svg += "</g>"
    svg += f'<path class="sc-wall" d="M{x0} {y0 - 8}V{y0 + rows * bh + 8}"/>'
    # смещение стыков между 1-м и 2-м рядом
    j1, j2 = x0 + 8 + bl, x0 + 8 + bl - 72
    yd = y0 + 2 * bh + 12
    svg += (f'<path class="sc-accent" d="M{j1} {y0}V{y0 + bh}M{j2} {y0 + bh}V{y0 + 2 * bh}"/>'
            f'<path class="sc-dim" d="M{j2} {yd}H{j1}M{j2} {yd - 6}V{yd + 6}M{j1} {yd - 6}V{yd + 6}"/>')
    yb = y0 + rows * bh + 34
    svg += callout((j1 + j2) / 2, yd, 210, yb, ["смещение стыков", "соседних рядов"])
    svg += callout(x0 + 4, y0 + rows * bh - 16, 40, yb, ["зазор", "у стены"])
    return figure(svg, "Укладка ламината со смещением рядов: стыки соседних рядов разнесены, у стены оставлен зазор",
                  "Стыки соседних рядов разносят, чтобы покрытие было прочнее; отрезок от последней доски ряда начинает следующий. "
                  "У стен оставляют компенсационный зазор — его закрывает плинтус. Минимальное смещение указано в инструкции к ламинату.",
                  "0 0 460 280")


# ---------- стяжка и наливной пол: разрез ----------

def _section(kind):
    x0, x1, base_top, level = 60, 430, 200, 120
    svg = (f'<pattern id="sc-conc" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           f'<path class="sc-hatch" d="M0 0V10"/></pattern>')
    # неровное основание: подложка + штриховка
    bumps = f"M{x0} {base_top}L140 {base_top - 12}L230 {base_top + 4}L330 {base_top - 18}L{x1} {base_top - 4}"
    base = f"{bumps}L{x1} {base_top + 60}L{x0} {base_top + 60}Z"
    svg += f'<path class="sc-basefill" d="{base}"/><path class="sc-base-top" d="{base}" fill="url(#sc-conc)"/>'
    # слой до уровня
    svg += f'<path class="sc-layer" d="M{x0} {level}H{x1}V{base_top - 4}L330 {base_top - 18}L230 {base_top + 4}L140 {base_top - 12}L{x0} {base_top}Z"/>'
    svg += f'<path class="sc-level" d="M{x0 - 14} {level}H{x1 + 14}"/>'
    # демпферная лента у стены
    svg += (f'<rect class="sc-wallbox" x="{x0 - 18}" y="44" width="18" height="{base_top + 60 - 44}"/>'
            f'<rect class="sc-tape" x="{x0}" y="{level - 12}" width="6" height="{base_top - level + 12}"/>')
    marks = (150, 280, 400)
    if kind == "screed":
        for mx in marks:
            gy = base_top - 14 if mx != 280 else base_top - 18
            svg += (f'<ellipse class="sc-mortar" cx="{mx}" cy="{gy}" rx="18" ry="{(gy - level) / 2 + 4}"/>'
                    f'<path class="sc-beacon" d="M{mx - 14} {level}H{mx + 14}M{mx} {level}V{level + 16}"/>')
        svg += callout(280, level - 2, 330, 52, "маяк")
        svg += callout(220, 150, 330, 84, "стяжка")
        svg += callout(150, base_top - 30, 170, 284, "раствор под маяк")
        level_text, label = "уровень по маякам", "Разрез стяжки: основание, маяки на растворе, слой стяжки до верха маяков и демпферная лента у стены"
        caption = ("Маяки выставляют по уровню на растворе, стяжку разравнивают правилом по их верху. "
                   "Толщину считают от верха маяков до основания, в среднем по нескольким точкам.")
    else:
        svg += f'<path class="sc-primer" d="{bumps}"/>'
        for mx in marks:
            svg += (f'<path class="sc-beacon" d="M{mx} {level}V{base_top - 14}M{mx - 9} {base_top - 4}L{mx} {base_top - 14}L{mx + 9} {base_top - 4}"/>'
                    f'<circle class="sc-dot" cx="{mx}" cy="{level}" r="4"/>')
        svg += callout(280, level, 320, 52, "репер (маячок)")
        svg += callout(220, 150, 320, 84, "наливной слой")
        svg += callout(230, base_top + 3, 250, 284, "грунтовка")
        level_text, label = "уровень по реперам", "Разрез наливного пола: основание с грунтовкой, реперы, наливной слой до уровня реперов и демпферная лента у стены"
        caption = ("Основание грунтуют, реперы выставляют по уровню, смесь разливают до их верха — она растекается сама. "
                   "Толщина в самом тонком и самом толстом месте — это то, что вводят в калькулятор.")
    svg += f'<text class="sc-t" x="{x0 + 12}" y="{level - 10}">{level_text}</text>'
    svg += callout(x0 + 3, level + 24, 16, 24, "демпферная лента")
    svg += f'<text class="sc-t sc-light" x="{(x0 + x1) / 2}" y="{base_top + 44}" text-anchor="middle">основание</text>'
    return figure(svg, label, caption, "0 0 460 300")


def screed_section():
    return _section("screed")


def selflevel_section():
    return _section("selflevel")
