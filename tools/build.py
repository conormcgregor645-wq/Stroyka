#!/usr/bin/env python3
"""Генератор страниц сайта «Метраж».

Все HTML-страницы, sitemap.xml и robots.txt собираются из этого файла:
общая шапка, меню, подвал, SEO-разметка и тексты. Запуск из корня репозитория:

    python3 tools/build.py

Зависимостей нет, нужен только Python 3. Готовые HTML лежат в репозитории,
поэтому для GitHub Pages ничего собирать не нужно — скрипт запускают только
после правок здесь. Правки, сделанные вручную прямо в HTML, при пересборке
затираются.
"""
import html
from html import escape as html_escape
import json
import math
import os
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse

# ===== НАСТРОЙКИ =====
# Базовый адрес сайта со слешем на конце. После переезда на свой домен
# поменяйте здесь и пересоберите: обновятся canonical, og:url, sitemap и robots.
SITE_URL = "https://metrazh.online/"
# Название сайта: шапка, подвал, og:site_name, заголовок страницы 404.
SITE_NAME = "Метраж"
# Контакт владельца сайта: страницы «О сайте» и «Политика конфиденциальности».
CONTACT_EMAIL = "franceone1@mail.ru"
# Дата для <lastmod> в sitemap.xml.
LASTMOD = "2026-10-12"
# Подтверждение сайта в партнёрской сети Mitgo (Admitad) — только на главной.
MITGO_VERIFY = '\n<meta name="mitgo-verification" content="5d60c4fe-cbf5-4f7c-a4eb-ab32dc9be0b9" />'
# Номер счётчика Метрики для <noscript> — тот же, что в assets/site.js.
metrika_counter = "113822395"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schemes  # noqa: E402  схемы для страниц (инлайн-SVG)

# Превью для соцсетей: assets/og/<страница>.png, 1200×630. Картинки рисует tools/og/render.cjs
# по списку tools/og/pages.json, который пишет этот скрипт.
OG_PAGES = []
# Иконки сайта: assets/favicon.svg (логотип-рулетка) и assets/apple-touch-icon.png (180×180).
ICONS_HEAD = ('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n'
              '<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">')
# Шрифты лежат в assets/fonts (@font-face — в начале assets/style.css). Заранее грузим
# два главных начертания: текст (Manrope 400) и заголовки (Manrope 800), кириллица.
FONTS_PRELOAD = "\n".join(f'<link rel="preload" href="assets/fonts/{f}.woff2" as="font" type="font/woff2" crossorigin>'
                          for f in ("manrope-cyrillic-400", "manrope-cyrillic-800"))

# Иконки материалов (линейные SVG из макета).
_SVG = '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#1E2226" stroke-width="1.6"{extra} aria-hidden="true">{body}</svg>'
ICONS = {
    "plitka": _SVG.format(extra=' stroke-linejoin="round"', body='<rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="8"/><rect x="3" y="13" width="8" height="8"/><rect x="13" y="13" width="8" height="8" fill="#D9622B"/>'),
    "oboi": _SVG.format(extra=' stroke-linejoin="round"', body='<path d="M5 4h11v16H5z"/><circle cx="16" cy="8" r="4" fill="#D9622B"/><path d="M8 8v8M11 8v8"/>'),
    "kraska": _SVG.format(extra=' stroke-linejoin="round"', body='<rect x="3" y="3" width="15" height="6" rx="1" fill="#D9622B"/><path d="M18 6h3v5h-9v3M10 14h4v7h-4z"/>'),
    "laminat": _SVG.format(extra=' stroke-linejoin="round"', body='<rect x="2" y="4" width="20" height="16"/><path d="M2 9.3h20M2 14.6h20M12 4v5.3M7 9.3v5.3M17 9.3v5.3M12 14.6V20"/><rect x="12" y="4" width="10" height="5.3" fill="#D9622B"/>'),
    "shtukaturka": _SVG.format(extra=' stroke-linejoin="round"', body='<path d="M3 15l9-9 9 9z" fill="#D9622B"/><path d="M12 15v6"/>'),
    "shpaklevka": _SVG.format(extra=' stroke-linejoin="round"', body='<path d="M4 4h16v7H4z" fill="#D9622B"/><path d="M12 11v4M10 15h4v6h-4z"/>'),
    "gipsokarton": _SVG.format(extra=' stroke-linejoin="round"', body='<rect x="4" y="2" width="16" height="20"/>' + "".join(
        f'<circle cx="{x}" cy="{y}" r="1" fill="#D9622B" stroke="none"/>' for y in (6, 12, 18) for x in (7, 17))),
    "uteplitel": _SVG.format(extra=' stroke-linecap="round"', body='<rect x="2" y="4" width="20" height="16" fill="#F7E2D5"/><path d="M2 9c3-2 5 2 10 0s7 2 10 0M2 15c3-2 5 2 10 0s7 2 10 0" stroke="#D9622B"/>'),
    "styazhka": _SVG.format(extra="", body='<rect x="2" y="14" width="20" height="6" fill="#D9622B"/><path d="M2 10h20M2 6h20"/>'),
    "kirpich": _SVG.format(extra="", body='<rect x="2" y="4" width="20" height="16"/><path d="M2 9.3h20M2 14.6h20M9 4v5.3M16 4v5.3M5.5 9.3v5.3M12.5 9.3v5.3M19 9.3v5.3M9 14.6V20M16 14.6V20"/><rect x="12.5" y="9.3" width="6.5" height="5.3" fill="#D9622B"/>'),
}

# Калькуляторы: файл, пункт меню, название на карточке, подпись на карточке.
CALCS = [
    ("plitka.html", "Плитка", "Плитка", "Штуки, клей, затирка"),
    ("oboi.html", "Обои", "Обои", "Рулоны с раппортом"),
    ("kraska.html", "Краска", "Краска", "Литры и грунтовка"),
    ("laminat.html", "Ламинат", "Ламинат", "Упаковки и подложка"),
    ("shtukaturka.html", "Штукатурка", "Штукатурка", "Мешки по толщине"),
    ("shpaklevka.html", "Шпаклёвка", "Шпаклёвка", "Старт и финиш"),
    ("gipsokarton.html", "Гипсокартон", "Гипсокартон", "Листы и профиль"),
    ("uteplitel.html", "Утеплитель", "Утеплитель", "Плиты и упаковки"),
    ("styazhka.html", "Стяжка", "Стяжка пола", "Смесь по толщине"),
    ("kirpich.html", "Кирпич", "Кирпич", "Штуки и раствор"),
]
# Статьи: файл, заголовок (H1), описание для списка, дата публикации (ISO), дата для людей.
ARTICLES = [
    ("skolko-plitki-na-vannuyu.html",
     "Сколько плитки нужно на ванную: готовые расчёты для 2×2, 2×3 и 3×3 м",
     "Таблица с плиткой, упаковками, клеем и затиркой для трёх типовых ванных, как измерить комнату, что вычесть и сколько брать запаса.",
     "2026-10-29T13:20:00+03:00", "29 октября 2026"),
]
ARTICLE_FILES = {a[0] for a in ARTICLES} | {"stati.html"}
# Хабы «Ремонт под ключ» и их общий список — пункт меню «Ремонт под ключ».
HUB_FILES = {"remont.html", "remont-vannoy.html", "remont-kuhni.html", "remont-komnaty.html"}

# В шапке — четыре главных калькулятора, текущий (если его среди них нет) и «Все калькуляторы».
NAV_MAIN = ["plitka.html", "oboi.html", "kraska.html", "laminat.html"]
CHECK = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A9481A" stroke-width="2.4" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>')
RULER = ('<svg class="logo-ruler" width="104" height="10" viewBox="0 0 104 10" aria-hidden="true">'
         '<rect x="0" y="0" width="104" height="10" rx="2" fill="#D9622B"/><g stroke="#1E2226" stroke-width="1.2">'
         + "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{6 if x == 6 else 7 if x == 56 else 4}"/>' for x in range(6, 100, 10))
         + "</g></svg>")


def icon(fn):
    return ICONS[fn.split(".")[0]]


def card(fn, name, desc):
    return f'<a class="card" href="{fn}">{icon(fn)}<span class="card-name">{name}</span><span class="card-desc">{desc}</span></a>'




# ---------- разметка полей формы ----------

def field(name, label, value, typ="text", extra="", show=None):
    im = ' inputmode="decimal"' if typ == "text" else ""
    sh = f' data-show="{show}"' if show else ""
    return (f'<div class="field"{sh}><label for="f-{name}">{label}</label>'
            f'<input id="f-{name}" name="{name}" type="{typ}"{im} value="{value}"{extra}></div>')


def select(name, label, options, selected, show=None):
    opts = "".join(f'<option value="{v}"{" selected" if v == selected else ""}>{t}</option>' for v, t in options)
    sh = f' data-show="{show}"' if show else ""
    return f'<div class="field"{sh}><label for="f-{name}">{label}</label><select id="f-{name}" name="{name}">{opts}</select></div>'


def seg(name, options, checked):
    out = '<div class="seg" role="radiogroup">'
    for v, t in options:
        c = " checked" if v == checked else ""
        out += f'<input type="radio" id="s-{name}-{v}" name="{name}" value="{v}"{c}><label for="s-{name}-{v}">{t}</label>'
    return out + "</div>"


def grid(*fields, cols=3, top=False):
    cls = "grid two" if cols == 2 else "grid"
    style = ' style="margin-top:12px"' if top else ""
    return f'<div class="{cls}"{style}>' + "".join(fields) + "</div>"


def h3(text):
    return f"<h3>{text}</h3>"


# Шаблоны комнат: длина, ширина, высота, проёмы (d — дверь, w — окно: ширина × высота). Обрабатывает calc.js.
PRESETS = [("Ванная 2×2", "2,2,2.5,d:0.7x2"), ("Санузел 1,5×1,5", "1.5,1.5,2.5,d:0.7x2"),
           ("Кухня 3×3", "3,3,2.5,d:0.8x2;w:1.5x1.5"), ("Комната 3×4", "3,4,2.5,d:0.8x2;w:1.5x1.5"),
           ("Комната 4×5", "4,5,2.5,d:0.8x2;w:1.5x1.5")]
PRESET_CHIPS = ('<div class="presets" role="group" aria-label="Шаблоны комнат">'
                + "".join(f'<button type="button" class="chip" data-preset="{v}">{t}</button>' for t, v in PRESETS) + "</div>")

ROOM3 = h3("Помещение") + PRESET_CHIPS + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3"), field("room_h", "Высота, м", "2.7"))
ROOM2 = h3("Помещение") + PRESET_CHIPS + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3"), cols=2)


def openings(show=None, hint="Площадь проёмов вычитается из площади стен."):
    sh = f' data-show="{show}"' if show else ""
    return (f'<div id="openings-block"{sh}><h3>Двери и окна</h3><div class="openings" id="openings"></div>'
            f'<p class="hint">{hint}</p><button type="button" class="btn" id="add-opening">+ Добавить проём</button></div>')


def reserve(options, selected, label="Запас на подрезку"):
    """Запас — кнопки-сегменты с подсказками. options: (значение %, подсказка)."""
    out = h3(label) + '<div class="seg-cards" role="radiogroup" aria-label="' + label + '">'
    for v, hint in options:
        c = " checked" if v == selected else ""
        out += (f'<input type="radio" id="s-reserve-{v}" name="reserve" value="{v}"{c}>'
                f'<label for="s-reserve-{v}"><b>{v}%</b><span>{hint}</span></label>')
    return out + "</div>"


def price(label):
    return field("price", label + " (необяз.)", "")


def calc_form(calc_type, inputs, plan_title):
    return f'''<div class="calc">
<form class="form-card" id="calc-form" data-calc="{calc_type}" autocomplete="off" novalidate aria-label="Параметры расчёта">
{inputs}
</form>
<aside class="calc-side" aria-label="Результат">
<section class="result-card" id="result" aria-live="polite"></section>
<section class="plan-card">
<div class="plan-head"><span class="plan-title">{plan_title}</span><span class="plan-label" id="plan-label"></span></div>
<svg id="plan" viewBox="0 0 340 240" role="img" aria-label="{plan_title}"></svg>
</section>
</aside>
</div>'''


def table(head, rows):
    out = '<div class="table-wrap"><table>\n<thead><tr>' + "".join(f'<th scope="col">{h}</th>' for h in head) + "</tr></thead>\n<tbody>\n"
    for r in rows:
        out += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>\n"
    return out + "</tbody></table></div>"


def ru(x, digits=0):
    s = f"{x:.{digits}f}".replace(".", ",")
    return s


AD_SLOT = '''<!-- Реклама РСЯ: ID блока (RSY_BLOCK_ID) задаётся в assets/site.js. Пока он не задан, блок скрыт. -->
<div class="ad-slot" data-rsy></div>'''


# ---------- шаблон страницы ----------

def faq_html(faq, open_cards=False):
    """Блок «Частые вопросы». На главной — открытые карточки, на калькуляторах — раскрывающиеся."""
    if open_cards:
        items = "".join(f'<div class="faq-card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faq)
    else:
        items = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq)
    return f'<h2>Частые вопросы</h2>\n<div class="faq">{items}</div>'


def nav_html(fn):
    files = list(NAV_MAIN)
    if fn in {c[0] for c in CALCS} and fn not in files:
        files.append(fn)
    labels = {c[0]: c[1] for c in CALCS}
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == fn else ""}>{labels[h]}</a>' for h in files)
    all_href = "#calc" if fn == "index.html" else "index.html#calc"
    articles = f'<a href="stati.html"{" aria-current=\"page\"" if fn in ARTICLE_FILES else ""}>Статьи</a>'
    remont = f'<a href="remont.html"{" aria-current=\"page\"" if fn in HUB_FILES else ""}>Ремонт под ключ</a>'
    return remont + links + articles + f'<a class="nav-all" href="{all_href}">Все калькуляторы</a>'


def page(fn, title, desc, main_html, faq=None, crumb=None, robots=None, in_sitemap=True, after_main="", verify="",
         trail=(), ld_extra=(), app=True, lastmod=None, og_title=None, og_icon=None, scripts=None):
    """trail — промежуточные крошки [(название, файл)]; ld_extra — дополнительная разметка Schema.org;
    app — добавлять WebApplication (для калькуляторов); lastmod — дата для sitemap;
    og_title — заголовок на превью для соцсетей (без него берётся превью главной)."""
    canon = SITE_URL + ("" if fn == "index.html" else fn)
    og_slug = fn[:-5] if og_title else "index"
    if og_title:
        OG_PAGES.append({"slug": og_slug, "title": og_title,
                         "icon": og_icon if og_icon is not None else ICONS.get(og_slug, "")})
    og_alt = html_escape(og_title or "Метраж — строительные калькуляторы")

    ld = []
    if crumb:
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE_URL}]
            + [{"@type": "ListItem", "position": i + 2, "name": n, "item": SITE_URL + h} for i, (n, h) in enumerate(trail)]
            + [{"@type": "ListItem", "position": len(trail) + 2, "name": crumb, "item": canon}]})
    ld.extend(ld_extra)
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    if crumb and app:
        ld.append({"@context": "https://schema.org", "@type": "WebApplication", "name": crumb, "url": canon,
                   "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any",
                   "offers": {"@type": "Offer", "price": "0", "priceCurrency": "RUB"}})
    ldhtml = "".join(f'\n<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)

    is_calc = fn in {c[0] for c in CALCS}
    if scripts is None:
        scripts = '\n<script src="assets/partners.js"></script>\n<script src="assets/calc.js"></script>' if is_calc else ""
    if fn == "spisok.html":
        scripts = '\n<script src="assets/partners.js"></script>\n<script src="assets/list.js"></script>'
    robots_meta = f'\n<meta name="robots" content="{robots}">' if robots else ""
    footer_links = ('<a href="index.html">Все калькуляторы</a><a href="remont.html">Ремонт под ключ</a><a href="stati.html">Статьи</a>'
                    + "".join(f'<a href="{h}">{t}</a>' for h, t, *_ in CALCS)
                    + '<a href="spisok.html">Список покупок</a><a href="o-sajte.html">О сайте</a><a href="privacy.html">Политика конфиденциальности</a>')
    host = urlparse(SITE_URL).hostname

    html = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">{robots_meta}
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE_URL}assets/og/{og_slug}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1E2226">
<meta name="color-scheme" content="light dark">
<link rel="manifest" href="site.webmanifest">
<!-- Подтверждение прав в Яндекс Вебмастере: раскомментируйте и вставьте код -->
<!-- <meta name="yandex-verification" content="YANDEX_VERIFICATION_CODE"> -->
<!-- Подтверждение прав в Google Search Console: раскомментируйте и вставьте код -->
<!-- <meta name="google-site-verification" content="GOOGLE_VERIFICATION_CODE"> -->{verify}
{ICONS_HEAD}
{FONTS_PRELOAD}
<link rel="stylesheet" href="assets/style.css">{ldhtml}
</head>
<body>
<header class="site-header"><div class="wrap header-bar">
<a class="logo" href="index.html"><span class="logo-name">{SITE_NAME}</span>{RULER}</a>
<a class="list-link" href="spisok.html" aria-label="Список покупок"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01" stroke-width="3"/></svg><span class="list-count" id="list-count" hidden>0</span></a>
<nav class="nav" aria-label="Основное меню">{nav_html(fn)}</nav>
</div></header>
{main_html}{after_main}
<footer class="site-footer"><div class="wrap">
<p class="footer-text"><strong>{SITE_NAME}</strong> · {host} — бесплатные строительные калькуляторы. Расчёты приблизительные, сверяйтесь с рекомендациями производителя.</p>
<span class="footer-copy">© 2026</span>
<nav class="footer-links" aria-label="Все калькуляторы">{footer_links}</nav>
</div></footer>
<!-- Яндекс Метрика: код счётчика в assets/site.js, здесь — запасной вариант без JavaScript -->
<noscript><div><img src="https://mc.yandex.ru/watch/{metrika_counter}" style="position:absolute; left:-9999px;" alt=""></div></noscript>
<script src="assets/site.js"></script>{scripts}
</body>
</html>
'''
    with open(os.path.join(ROOT, fn), "w", encoding="utf-8") as f:
        f.write(html)
    if in_sitemap:
        SITEMAP.append((canon, lastmod or LASTMOD))


SITEMAP = []

MBAR = '''
<div class="mbar" id="mbar" aria-hidden="true">
<span class="mbar-main"><span class="mbar-cap">Нужно купить</span><span class="mbar-big" id="mbar-big">—</span></span>
<span class="mbar-sub" id="mbar-sub"></span>
</div>'''


# Значения полей калькуляторов по умолчанию и их страницы — для хабов «Ремонт под ключ»:
# хаб считает этапы теми же формулами (assets/calc.js) с теми же значениями, что и калькулятор.
CALC_DEFAULTS = {}
CALC_PAGES = {}
CALC_OPENINGS = set()   # калькуляторы с блоком «Двери и окна»


def form_defaults(inputs):
    values = {}
    for name, value in re.findall(r'<input id="f-[^"]+" name="([^"]+)" type="[^"]+"[^>]*? value="([^"]*)"', inputs):
        values[name] = value
    for name, value in re.findall(r'<input type="radio" id="[^"]+" name="([^"]+)" value="([^"]*)" checked>', inputs):
        values[name] = value
    for name, opts in re.findall(r'<select id="f-[^"]+" name="([^"]+)">(.*?)</select>', inputs):
        m = re.search(r'<option value="([^"]*)" selected>', opts) or re.search(r'<option value="([^"]*)"', opts)
        values[name] = m.group(1)
    return values


# Ссылки «Весь ремонт …» с калькуляторов на хабы.
HUB_LINKS = {"plitka.html": ("remont-vannoy.html", "Весь ремонт ванной"),
             "styazhka.html": ("remont-vannoy.html", "Весь ремонт ванной")}


def calc_page(fn, title, desc, h1, calc_type, buy_title, plan_title, inputs, how, norms, faq, related=""):
    """Страница калькулятора: форма и результат, схема, покупка, реклама, «Как считается», нормы, FAQ."""
    CALC_DEFAULTS[calc_type] = form_defaults(inputs)
    CALC_PAGES[calc_type] = fn
    if 'id="openings"' in inputs:
        CALC_OPENINGS.add(calc_type)
    hub = HUB_LINKS.get(fn)
    hub_html = f'\n<p class="hub-link"><a href="{hub[0]}">{hub[1]} →</a></p>' if hub else ""
    main = f'''<main class="wrap calc-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><span>{h1}</span></nav>
<div class="calc-head"><h1>{h1}</h1><span class="calc-tagline">Формулы как у мастеров · Без регистрации</span></div>
{calc_form(calc_type, inputs, plan_title)}{hub_html}
<section class="buy-card" id="buy" data-title="{buy_title}"></section>
{AD_SLOT}
<article class="article">
<h2>Как считается</h2>
{how}
<h2>Нормы расхода</h2>
{norms}
{related}
{faq_html(faq)}
</article>
</main>'''
    page(fn, title, desc, main, faq, crumb=h1, after_main=MBAR, og_title=h1)


# ---------- главная ----------

def build_index():
    pills = "".join(f'<span class="pill">{CHECK}{t}</span>'
                    for t in ("Формулы как у мастеров", "Учитываем окна и двери", "Бесплатно, без регистрации"))
    cards = "".join(card(h, name, d) for h, _, name, d in CALCS)
    faq = [("Насколько точен расчёт?", "Калькуляторы используют те же формулы, что и мастера: площадь поверхности за вычетом проёмов плюс запас на подрезку. Итог округляется вверх до целых штук, рулонов, мешков и упаковок."),
           ("Почему всегда нужен запас?", "Материал режется по краям и бьётся при подрезке, а через месяц ту же партию можно уже не найти: оттенок у разных партий отличается. Поэтому закладываем 5–15% в зависимости от укладки."),
           ("Нужно ли вводить размеры в каждом калькуляторе?", "Нет. Длина, ширина и высота комнаты сохраняются в браузере и подставляются в другие калькуляторы автоматически."),
           ("Можно ли сохранить расчёт?", "Да. Кнопка «Поделиться» отправляет ссылку со всеми введёнными значениями, а «Распечатать» выводит результат на бумагу без лишних элементов страницы.")]
    steps = [("01", "Выберите материал", "Плитка, обои, ламинат или любой из десяти калькуляторов."),
             ("02", "Введите размеры", "Длина, ширина, высота, окна и двери. Размеры запоминаются для других калькуляторов."),
             ("03", "Идите в магазин", "Штуки, упаковки и мешки, округлённые вверх. Распечатайте или отправьте ссылкой.")]
    steps_html = "".join(f'<div class="step"><span class="step-num">{n}</span><h3>{t}</h3><p>{d}</p></div>' for n, t, d in steps)
    # Пример: пол 3×2 м, плитка 30×30, запас 10% → 74 плитки, по 11 шт. в упаковке → 7 упаковок.
    demo_svg = '''<svg viewBox="0 0 340 200" role="img" aria-label="План пола 3 на 2 метра, разложенный плиткой 30 на 30 сантиметров">
<defs><pattern id="hTiles" x="40" y="30" width="26" height="26" patternUnits="userSpaceOnUse"><rect class="pl-floor" width="26" height="26"/><path d="M26 0V26H0" fill="none" stroke="#D9622B" stroke-width="1"/></pattern></defs>
<rect class="pl-edge" x="40" y="30" width="260" height="156" style="fill:url(#hTiles)"/>
<g class="pl-dim"><line x1="40" y1="14" x2="300" y2="14"/><line x1="40" y1="9" x2="40" y2="19"/><line x1="300" y1="9" x2="300" y2="19"/><line x1="316" y1="30" x2="316" y2="186"/><line x1="311" y1="30" x2="321" y2="30"/><line x1="311" y1="186" x2="321" y2="186"/></g>
<rect x="148" y="5" width="44" height="18" class="pl-box"/><text x="170" y="18" text-anchor="middle" class="svg-num">3,0 м</text>
<rect x="303" y="99" width="30" height="18" class="pl-box"/><text x="318" y="112" text-anchor="middle" class="svg-num">2,0</text>
</svg>'''
    main = f'''<main>
<section class="wrap home-hero" id="calc">
<h1>Сколько материала нужно на&nbsp;ремонт?</h1>
<div class="pills">{pills}</div>
<h2 class="home-sub">Ремонт под ключ <a href="remont.html">все этапы →</a></h2>
<div class="cards hub-cards">{"".join(hub_card(h) for h in HUBS)}</div>
<h2 class="home-sub">Калькуляторы материалов</h2>
<div class="cards">{cards}</div>
</section>
<section class="wrap demo">
<div class="demo-text">
<span class="eyebrow">Как это выглядит</span>
<h2>Вводите размеры и сразу видите, сколько покупать</h2>
<p>Калькулятор рисует комнату в масштабе, раскладывает материал и округляет итог вверх до целых упаковок. Расчёт можно отправить мастеру или распечатать для магазина.</p>
<a class="btn-primary" href="plitka.html">Попробовать на плитке</a>
</div>
<div class="demo-card">
<div class="demo-head"><span class="demo-title">Пол ванной</span><span class="demo-meta">плитка 30×30</span></div>
{demo_svg}
<div class="demo-total"><span class="demo-big">74 плитки</span><span class="demo-sub">7 упаковок по 11 шт. · запас 10%</span></div>
</div>
</section>
<section class="steps"><div class="wrap">
<h2>Три шага до списка покупок</h2>
<div class="steps-grid">{steps_html}</div>
</div></section>
<section class="wrap useful">
<h2>Полезное</h2>
<div class="posts">{"".join(article_card(a) for a in ARTICLES)}</div>
</section>
<section class="wrap home-faq">
{faq_html(faq, open_cards=True)}
</section>
</main>'''
    page("index.html",
         "Калькулятор ремонта — расчёт плитки, обоев, краски, штукатурки и других материалов",
         "Бесплатные строительные калькуляторы: плитка, обои, краска, ламинат, штукатурка, шпаклёвка, гипсокартон, утеплитель, стяжка и кирпич. С учётом окон, дверей и запаса.",
         main, faq, verify=MITGO_VERIFY, og_title="Сколько материала нужно на ремонт?")


# ---------- калькуляторы ----------

def build_tile():
    inputs = (h3("Что облицовываем") + seg("surface", [("floor", "Пол"), ("walls", "Стены"), ("both", "Пол и стены")], "floor")
              + ROOM3 + openings("surface:walls,both")
              + h3("Плитка") + grid(field("tile_w", "Ширина, см", "30"), field("tile_h", "Длина, см", "60"),
                                    field("per_pack", "Штук в упаковке", "8", "number", ' min="0" step="1"'))
              + grid(field("joint", "Шов, мм", "2"), field("thickness", "Толщина, мм", "9"), top=True)
              + reserve([("5", "крупная комната"), ("10", "прямая укладка"), ("15", "диагональ"), ("20", "сложная")], "10")
              + grid(price("Цена, ₽ за м²"), top=True))
    how = '''<p>Площадь пола — длина × ширина. Площадь стен — периметр × высота минус площадь дверей и окон. Площадь делится на площадь одной плитки и увеличивается на запас: 10% при прямой укладке и 15% при диагональной. Результат округляется вверх до целой плитки, а затем — до целых упаковок.</p>
<p>Затирка считается по формуле: (A + B) / (A × B) × толщина плитки × ширина шва × 1,6 кг/м², где A и B — стороны плитки в мм, 1,6 — плотность смеси. Калькулятор добавляет 10% запаса.</p>'''
    how += schemes.bath_measure() + schemes.tile_layouts()
    norms = table(["Размер плитки", "Зубчатый шпатель", "Клей, кг/м²"],
                  [["до 20 см", "6 мм", "≈ 3,5"], ["20–40 см", "8 мм", "≈ 4,5"], ["больше 40 см", "10–12 мм", "≈ 6"]])
    calc_page("plitka.html",
              "Калькулятор плитки — сколько нужно плитки, клея и затирки на пол и стены",
              "Онлайн-калькулятор плитки: количество плиток и упаковок для пола и стен ванной, расход плиточного клея и затирки с учётом швов и запаса.",
              "Калькулятор плитки",
              "tile", "Купить плитку и клей", "Схема пола", inputs, how, norms,
              [("Какой запас плитки брать?", "При прямой укладке — 10%, при диагональной — 15%, для сложных раскладок (ёлочка, модульная) — до 20%. Для крупного формата от 60×60 запас лучше не уменьшать: такую плитку сложно резать без сколов."),
               ("Как посчитать плитку для ванной?", "Выберите «Пол и стены», введите размеры ванной и добавьте дверь. Если стены облицовываются не до потолка, укажите вместо высоты комнаты высоту укладки."),
               ("Сколько клея нужно на 1 м² плитки?", "В среднем 3,5–6 кг на м² в зависимости от размера плитки и ровности основания. Точный расход указан на мешке клея.")],
              related='<h2>По теме</h2>\n<div class="posts">' + article_card(ARTICLES[0]) + "</div>")


def build_wallpaper():
    inputs = (ROOM3 + openings()
              + h3("Рулон") + grid(select("roll_w", "Ширина рулона", [("0.53", "0,53 м"), ("0.7", "0,70 м"), ("1.06", "1,06 м")], "1.06"),
                                   field("roll_l", "Длина рулона, м", "10.05"), field("rapport", "Раппорт, см", "0"))
              + h3("Подгонка рисунка") + seg("match", [("none", "Без подгонки"), ("straight", "Прямая"), ("offset", "Со смещением")], "none")
              + grid(price("Цена рулона, ₽"), top=True))
    how = '''<ol>
<li>Считаем площадь стен без окон и дверей и делим её на высоту — получаем ширину, которую нужно оклеить.</li>
<li>Делим эту ширину на ширину рулона и округляем вверх — получаем число полос.</li>
<li>Длина полосы — высота стены плюс 10 см на подрезку. Если у обоев есть раппорт, длина округляется вверх до целого числа раппортов, а при подгонке со смещением добавляется ещё полраппорта.</li>
<li>Считаем, сколько целых полос выходит из рулона, и делим на это число количество полос с округлением вверх.</li>
</ol>
<p>Раппорт — расстояние, через которое повторяется рисунок. Он указан на этикетке рулона числом в сантиметрах. Значок со сдвинутыми стрелками означает подгонку со смещением, «0» или стрелка без числа — обои без подгонки.</p>'''
    how += schemes.wallpaper_rapport()
    norms = (table(["Комната, высота 2,7 м", "Рулоны 0,53×10,05 м", "Рулоны 1,06×10,05 м"],
                   [["3×3 м (9 м²)", "7", "4"], ["3×4 м (12 м²)", "8", "4"], ["4×5 м (20 м²)", "11", "6"]])
             + "\n<p>Для обоев без подгонки рисунка, с одной дверью 0,8×2 м и одним окном 1,4×1,5 м. Обойного клея — 1 пачка на 20–30 м² стен.</p>")
    calc_page("oboi.html",
              "Калькулятор обоев — сколько рулонов нужно на комнату",
              "Рассчитайте, сколько рулонов обоев нужно на комнату: учёт раппорта, ширины рулона 0,53 или 1,06 м, окон и дверей. Клей и обрезки.",
              "Калькулятор обоев",
              "wallpaper", "Купить обои и клей", "План комнаты", inputs, how, norms,
              [("Сколько рулонов обоев нужно на комнату 18 м²?", "Для комнаты 3×6 м с потолком 2,7 м и метровыми обоями без подгонки — около 6 рулонов. С раппортом 64 см и подгонкой понадобится больше: введите параметры в калькулятор."),
               ("Какие обои выгоднее — 0,53 или 1,06 м?", "Метровые клеить быстрее, швов вдвое меньше. Но в маленьких комнатах с большим количеством углов и проёмов от узких рулонов остаётся меньше обрезков."),
               ("Нужно ли вычитать окна и двери?", "Да, калькулятор вычитает их площадь. Обрезки обычно уходят на участки над дверью и под окном, поэтому отдельный запас на них не нужен.")])


def build_paint():
    inputs = (h3("Что красим") + seg("surface", [("walls", "Стены"), ("ceiling", "Потолок"), ("both", "Стены и потолок")], "walls")
              + ROOM3 + openings("surface:walls,both")
              + h3("Краска") + grid(select("layers", "Слоёв", [("1", "1"), ("2", "2"), ("3", "3")], "2"),
                                    field("coverage", "Расход, м²/л на слой", "9"),
                                    select("can", "Объём тары", [("0.9", "0,9 л"), ("2.5", "2,5 л"), ("2.7", "2,7 л"), ("4.5", "4,5 л"),
                                                                 ("5", "5 л"), ("9", "9 л"), ("10", "10 л")], "9"))
              + reserve([("0", "без запаса"), ("5", "ровные стены"), ("10", "обычно"), ("15", "пористая поверхность")], "10", "Запас")
              + grid(price("Цена тары, ₽"), top=True)
              + '<p class="hint">Расход указан на банке: обычно 8–12 м² на литр для одного слоя. Для тёмных цветов и фактурных стен берите меньшее значение.</p>')
    how = '''<p>Литры = площадь × количество слоёв ÷ расход (м²/л) + запас. Площадь стен — периметр × высота минус окна и двери, площадь потолка равна площади пола. Результат округляется вверх до 0,1 л, количество банок — вверх до целых.</p>
<p>Перед покраской стены грунтуют: грунтовка уменьшает впитываемость и экономит до трети краски.</p>'''
    norms = table(["Тип краски", "Расход на 1 слой"],
                  [["Водоэмульсионная для потолка", "6–8 м²/л"], ["Интерьерная акриловая для стен", "8–12 м²/л"],
                   ["Латексная моющаяся", "10–12 м²/л"], ["Алкидная эмаль", "10–14 м²/л"], ["Грунтовка", "≈ 10 м²/л"]])
    calc_page("kraska.html",
              "Калькулятор краски — сколько литров нужно на стены и потолок",
              "Онлайн-расчёт краски для стен и потолка: литры и количество банок с учётом слоёв, расхода, окон и дверей. Плюс грунтовка и малярный скотч.",
              "Калькулятор краски",
              "paint", "Купить краску и грунтовку", "План комнаты", inputs, how, norms,
              [("Сколько слоёв краски наносить?", "Обычно два. Один слой допустим при обновлении того же цвета, три — при перекрашивании тёмной стены в светлый цвет."),
               ("Сколько краски нужно на 1 м² стены?", "При двух слоях и расходе 10 м²/л — около 0,2 л на квадратный метр."),
               ("Что значит расход на банке?", "Это площадь, которую покрывает литр краски в один слой на ровной загрунтованной поверхности. На шероховатых и непрогрунтованных стенах расход выше.")])


def build_laminate():
    inputs = (ROOM2
              + h3("Ламинат") + grid(field("pack", "Площадь в упаковке, м²", "2.131"),
                                     field("board_l", "Длина доски, мм", "1380"), field("board_w", "Ширина доски, мм", "193"))
              + reserve([("5", "прямая, простая комната"), ("7", "прямая укладка"), ("10", "сложная комната"), ("15", "диагональ")], "7", "Укладка и запас")
              + grid(price("Цена упаковки, ₽"), top=True)
              + h3("Двери, подложка, плинтус") + grid(field("doors", "Дверей", "1", "number", ' min="0" step="1"'), field("door_w", "Ширина двери, м", "0.8"))
              + grid(field("underlay", "Подложка в рулоне, м²", "10"), field("plinth", "Длина плинтуса, м", "2.5"), cols=2, top=True))
    how = '''<p>Площадь пола умножается на коэффициент подрезки (5–7% для прямой укладки, около 15% для диагональной) и делится на площадь одной упаковки. Результат округляется вверх до целой упаковки. Площадь в упаковке указана на торце коробки.</p>
<p>Подложку кладут встык по всей площади, калькулятор добавляет 5% на подрезку. Длина плинтуса — периметр комнаты минус ширина дверных проёмов, тоже с 5% запаса.</p>'''
    how += schemes.laminate_rows()
    norms = table(["Способ укладки", "Запас на подрезку"],
                  [["Прямая, прямоугольная комната", "5–7%"], ["Прямая, много углов и выступов", "10%"],
                   ["Диагональная", "15%"], ["Подложка", "+5%"], ["Плинтус", "+5% по длине"]])
    calc_page("laminat.html",
              "Калькулятор ламината — сколько упаковок нужно на комнату",
              "Рассчитайте ламинат на комнату: количество упаковок с учётом способа укладки, подложка, плинтус, заглушки и порожки.",
              "Калькулятор ламината",
              "laminate", "Купить ламинат и подложку", "Схема пола", inputs, how, norms,
              [("Какой запас ламината брать?", "5–7% при прямой укладке и 10–15% при диагональной или в комнате со множеством выступов."),
               ("Сколько ламината нужно на 20 м²?", "При упаковке 2,131 м² и прямой укладке с запасом 7% — 11 упаковок."),
               ("Нужно ли учитывать площадь под мебелью?", "Да. Ламинат — плавающее покрытие, его укладывают по всей комнате, включая места под шкафами.")])


SURFACE3 = [("walls", "Стены"), ("ceiling", "Потолок"), ("both", "Стены и потолок")]


def build_plaster():
    inputs = (h3("Что штукатурим") + seg("surface", SURFACE3, "walls")
              + ROOM3 + openings("surface:walls,both")
              + h3("Смесь") + grid(select("mix", "Тип штукатурки", [("0.9", "Гипсовая"), ("1.7", "Цементная"), ("1.5", "Цементно-известковая")], "0.9"),
                                   field("thickness", "Средний слой, мм", "15"),
                                   select("bag", "Мешок", [("25", "25 кг"), ("30", "30 кг")], "30"))
              + reserve([("5", "ровные стены"), ("10", "рекомендуем"), ("15", "сложные стены")], "10", "Запас")
              + grid(price("Цена мешка, ₽"), top=True)
              + '<p class="hint">Средний слой — разница между самой выступающей и самой утопленной точкой стены, делённая на два, плюс 5 мм над маяком.</p>')
    how = '''<p>Масса смеси = площадь × средняя толщина слоя (мм) × расход на 1 мм + запас. Количество мешков округляется вверх. Площадь стен — периметр × высота минус окна и двери, площадь потолка равна площади пола.</p>
<p>Маяки ставят вертикально с шагом не больше 1,5 м, чтобы двухметровое правило всегда опиралось на два маяка, плюс по одному у каждого угла. Грунтовку закладываем из расчёта 0,15 л на м².</p>'''
    norms = table(["Штукатурка", "Расход на 1 мм", "При слое 10 мм", "Обычный слой"],
                  [["Гипсовая", "0,8–1 кг/м²", "8–10 кг/м²", "5–50 мм"], ["Цементная", "1,6–1,8 кг/м²", "16–18 кг/м²", "10–30 мм"],
                   ["Цементно-известковая", "1,4–1,6 кг/м²", "14–16 кг/м²", "10–30 мм"]])
    calc_page("shtukaturka.html",
              "Калькулятор штукатурки — расход на стены и потолок, сколько мешков",
              "Калькулятор штукатурки онлайн: сколько мешков гипсовой или цементной штукатурки нужно на стены и потолок, маяки и грунтовка с учётом толщины слоя.",
              "Калькулятор штукатурки",
              "plaster", "Купить штукатурку и маяки", "План комнаты", inputs, how, norms,
              [("Как определить толщину слоя штукатурки?", "Приложите к стене правило или натяните нить и найдите самую выступающую и самую утопленную точки. Средний слой — половина разницы между ними плюс 5–6 мм толщины маяка."),
               ("Сколько штукатурки нужно на 1 м² стены?", "Гипсовой — около 9 кг при слое 10 мм, цементной — около 17 кг. Точный расход указан на мешке."),
               ("Какую штукатурку выбрать — гипсовую или цементную?", "Гипсовая подходит для сухих комнат: легче наносится и не требует финишной шпаклёвки под обои. Цементная — для ванных, кухонь и неотапливаемых помещений."),
               ("Сколько маяков нужно на комнату?", "Маяки ставят с шагом до 1,5 м и по одному у каждого угла: на комнату 4×3 м обычно уходит 14 маяков длиной 3 м.")])


def build_putty():
    inputs = (h3("Что шпаклюем") + seg("surface", SURFACE3, "walls")
              + ROOM3 + openings("surface:walls,both")
              + h3("Стартовый слой") + grid(field("start_mm", "Толщина, мм", "2"), field("start_rate", "Расход, кг/м² на 1 мм", "1"),
                                            field("start_bag", "Мешок, кг", "25"))
              + h3("Финишный слой") + grid(field("finish_mm", "Толщина, мм", "1"), field("finish_rate", "Расход, кг/м² на 1 мм", "1.2"),
                                           field("finish_bag", "Мешок, кг", "20"))
              + reserve([("5", "ровные стены"), ("10", "рекомендуем"), ("15", "сложные стены")], "10", "Запас")
              + '<p class="hint">Поставьте толщину 0, если слой не нужен: например, по ровной штукатурке хватает одного финиша.</p>')
    how = '''<p>Для каждого слоя: масса = площадь × толщина (мм) × расход на 1 мм + запас. Мешки округляются вверх отдельно для стартовой и финишной шпаклёвки.</p>
<p>Перед каждым слоем стену грунтуют — около 0,1 л на м². Абразивная сетка: примерно 1 лист на 10 м² шлифовки.</p>'''
    norms = table(["Шпаклёвка", "Расход на 1 мм", "Слой за проход"],
                  [["Стартовая гипсовая", "0,9–1,1 кг/м²", "до 5 мм"], ["Стартовая цементная", "1,4–1,6 кг/м²", "до 5 мм"],
                   ["Финишная гипсовая", "0,9–1,1 кг/м²", "0,5–2 мм"], ["Финишная полимерная", "1,1–1,3 кг/м²", "0,2–1,5 мм"],
                   ["Готовая паста", "1,5–1,7 кг/м²", "0,2–1 мм"]])
    calc_page("shpaklevka.html",
              "Калькулятор шпаклёвки — расход стартовой и финишной шпаклёвки на м²",
              "Калькулятор шпаклёвки для стен и потолка: сколько килограммов и мешков стартовой и финишной шпаклёвки нужно на комнату, грунтовка и абразив.",
              "Калькулятор шпаклёвки",
              "putty", "Купить шпаклёвку", "План комнаты", inputs, how, norms,
              [("Сколько шпаклёвки нужно на 1 м² стены?", "Финишной — около 1–1,2 кг при слое 1 мм, стартовой — 2–3 кг при слое 2–3 мм."),
               ("Нужна ли стартовая шпаклёвка?", "Если стена оштукатурена по маякам или это гипсокартон, обычно хватает финиша. Стартовая нужна, чтобы убрать неровности 1–5 мм."),
               ("Сколько слоёв финишной шпаклёвки наносить?", "Обычно два тонких слоя по 0,5–1 мм. Под покраску стену после второго слоя шлифуют и проверяют на свет."),
               ("Почему расход больше, чем на мешке?", "Производитель указывает расход для идеально ровного основания. На реальной стене часть смеси уходит в неровности и при шлифовке, поэтому калькулятор добавляет запас.")])


def build_drywall():
    inputs = (h3("Что монтируем") + seg("mode", [("walls", "Обшивка стен"), ("partition", "Перегородка"), ("ceiling", "Потолок")], "walls")
              + ROOM3
              + grid(field("part_l", "Длина перегородки, м", "3", show="mode:partition"), top=True)
              + openings("mode:walls,partition", "Площадь проёмов вычитается из площади обшивки.")
              + h3("Лист и каркас") + grid(select("sheet", "Лист ГКЛ", [("3", "2500×1200 мм"), ("3.6", "3000×1200 мм"), ("2.4", "2000×1200 мм")], "3"),
                                           select("layers", "Слоёв листов", [("1", "1"), ("2", "2")], "1"),
                                           select("step", "Шаг профиля", [("0.6", "600 мм"), ("0.4", "400 мм")], "0.6"))
              + grid(select("profile_len", "Длина профиля", [("3", "3 м"), ("4", "4 м")], "3"), price("Цена листа, ₽"), top=True)
              + reserve([("5", "простая форма"), ("10", "рекомендуем"), ("15", "много проёмов")], "10"))
    how = '''<p>Листы: площадь обшивки × число слоёв + запас, делённые на площадь листа, с округлением вверх. Перегородку обшивают с двух сторон.</p>
<ul>
<li><b>Обшивка стен:</b> стойки ПП 60×27 с выбранным шагом вдоль каждой стены плюс по одной у угла, направляющий ПН 28×27 по полу и потолку, прямые подвесы с шагом до 1 м по высоте стойки.</li>
<li><b>Перегородка:</b> стойки ПС 50×50 с шагом 600 или 400 мм, направляющий ПН 50×40 по полу и потолку.</li>
<li><b>Потолок:</b> ПН 28×27 по периметру, линии ПП 60×27 поперёк короткой стороны, подвесы с шагом до 1 м. Расчёт для одноуровневого каркаса.</li>
</ul>
<p>Саморезы по ГКЛ: 20 шт/м² на стенах и 25 шт/м² на потолке для каждого слоя. Клопы: 2 на подвес и 4 на стойку. Дюбель-гвозди: каждые 50 см направляющей и 2 на подвес.</p>'''
    norms = table(["Материал", "Стена / перегородка", "Потолок"],
                  [["Саморезы 3,5×25 по ГКЛ", "≈ 20 шт/м² на слой", "≈ 25 шт/м²"], ["Профиль ПП / ПС", "≈ 2 м/м²", "≈ 1,7 м/м²"],
                   ["Прямой подвес", "≈ 1,2 шт/м² (только обшивка)", "≈ 1,2–1,7 шт/м²"], ["Серпянка", "≈ 1,2 м/м²", "≈ 1,2 м/м²"],
                   ["Шпаклёвка для швов", "≈ 0,35 кг/м²", "≈ 0,35 кг/м²"]])
    calc_page("gipsokarton.html",
              "Калькулятор гипсокартона — листы, профиль, подвесы и саморезы",
              "Калькулятор гипсокартона онлайн: сколько листов ГКЛ, профиля ПП и ПН, подвесов, саморезов и дюбелей нужно на обшивку стен, перегородку или потолок.",
              "Калькулятор гипсокартона",
              "drywall", "Купить гипсокартон и профиль", "План комнаты", inputs, how, norms,
              [("Какой шаг профиля выбрать?", "Стандартный шаг стоек — 600 мм, под ширину листа 1200 мм. Шаг 400 мм делают под тяжёлую плитку, в двухслойной обшивке потолка и при высоте стены больше 3 м."),
               ("Сколько саморезов нужно на лист гипсокартона?", "На лист 2500×1200 уходит 60–75 саморезов: шаг 25 см по краям и 30 см в середине листа."),
               ("Какой гипсокартон взять для ванной?", "Влагостойкий ГКЛВ (зелёный) толщиной 12,5 мм. Для потолка подойдёт и облегчённый 9,5 мм."),
               ("Нужен ли запас гипсокартона?", "Да, 5–10%: листы ломаются при переноске, а подрезка у проёмов и углов даёт обрезки, которые не всегда удаётся использовать.")])


def build_insulation():
    inputs = (h3("Что утепляем") + seg("surface", [("walls", "Стены"), ("one", "Одна стена"), ("floor", "Пол или перекрытие")], "walls")
              + ROOM3 + openings("surface:walls,one")
              + h3("Утеплитель") + grid(select("total_mm", "Толщина утепления", [("50", "50 мм"), ("100", "100 мм"), ("150", "150 мм"), ("200", "200 мм")], "100"),
                                        field("board_t", "Толщина плиты, мм", "50"), field("per_pack", "Плит в упаковке", "8", "number", ' min="0" step="1"'))
              + grid(field("board_l", "Длина плиты, мм", "1200"), field("board_w", "Ширина плиты, мм", "600"),
                     price("Цена упаковки, ₽"), top=True)
              + reserve([("3", "минимум"), ("5", "рекомендуем"), ("10", "сложная форма")], "5"))
    how = '''<p>Число слоёв = требуемая толщина ÷ толщина плиты (вверх). Плиты = площадь × слои + запас, делённые на площадь одной плиты, с округлением вверх. Затем плиты пересчитываются в упаковки.</p>
<p>Пароизоляцию кладут с нахлёстом 10 см — плюс 10% к площади. Для стен добавляем тарельчатые дюбели — около 6 штук на м².</p>
<p>Режим «Одна стена» — для наружной стены комнаты: площадь равна длине × высоте минус её окна и двери. Длину стены введите в поле «Длина».</p>'''
    norms = table(["Материал", "Типовая плита", "В упаковке"],
                  [["Минвата (плиты)", "1200×600×50 мм", "8–12 шт. (5,76–8,64 м²)"], ["Минвата (плиты)", "1200×600×100 мм", "4–6 шт."],
                   ["Пенополистирол", "1000×1000×50 мм", "10–12 шт."], ["Экструдированный пенополистирол", "1200×600×50 мм", "8 шт."],
                   ["Дюбели для стен", "—", "5–6 шт/м²"]])
    calc_page("uteplitel.html",
              "Калькулятор утеплителя — сколько плит и упаковок нужно",
              "Калькулятор утеплителя: сколько плит и упаковок минваты или пенополистирола нужно на стены, пол или перекрытие, объём в м³, пароизоляция и дюбели.",
              "Калькулятор утеплителя",
              "insulation", "Купить утеплитель", "План комнаты", inputs, how, norms,
              [("Какую толщину утеплителя выбрать?", "Для стен в средней полосе России обычно хватает 100–150 мм минваты, для перекрытий и мансард — 150–200 мм. Точную толщину даёт теплотехнический расчёт по СП 50.13330."),
               ("Как пересчитать утеплитель в кубометры?", "Площадь × толщину в метрах: 30 м² × 0,1 м = 3 м³. Калькулятор показывает объём, а на упаковке указаны и площадь, и объём."),
               ("Нужна ли пароизоляция?", "При утеплении изнутри и в каркасных конструкциях — да, с тёплой стороны. Без неё влага из комнаты конденсируется в утеплителе."),
               ("Почему два слоя по 50 мм лучше одного 100 мм?", "Второй слой кладут со смещением, и он перекрывает стыки первого — так не остаётся сквозных щелей и мостиков холода.")])


def build_screed():
    inputs = (ROOM2
              + h3("Стяжка") + grid(field("thickness", "Средняя толщина, мм", "50"))
              + reserve([("5", "рекомендуем"), ("10", "неровное основание")], "5", "Запас")
              + h3("Материал") + seg("mix", [("ready", "Готовая сухая смесь"), ("diy", "Цемент и песок")], "ready")
              + grid(select("rate", "Смесь", [("2", "ЦПС М150 (2 кг/м²·мм)"), ("2.2", "Пескобетон М300 (2,2 кг/м²·мм)"),
                                              ("1.6", "Наливной пол (1,6 кг/м²·мм)")], "2", show="mix:ready"),
                     select("bag", "Мешок", [("25", "25 кг"), ("40", "40 кг"), ("50", "50 кг")], "40", show="mix:ready"),
                     field("price", "Цена мешка, ₽ (необяз.)", "", show="mix:ready"),
                     select("ratio", "Пропорция цемент : песок", [("3", "1 : 3 (М150)"), ("4", "1 : 4 (М100)")], "3", show="mix:diy"),
                     top=True)
              + '<p class="hint">Средняя толщина — от нулевого уровня (верх маяков) до основания, усреднённая по замерам в нескольких точках.</p>')
    how = '''<p><b>Готовая смесь:</b> масса = площадь × толщина (мм) × расход на 1 мм + запас, количество мешков — вверх до целых.</p>
<p><b>Цемент и песок:</b> объём раствора = площадь × толщина. Сухих компонентов на 1 м³ раствора нужно 1,3 м³ — смесь уплотняется при затворении. При пропорции 1 : 3 это 0,325 м³ цемента (≈ 422 кг при насыпной плотности 1300 кг/м³) и 0,975 м³ песка. Фиброволокно — 0,9 кг на м³.</p>
<p>Демпферную ленту клеят по периметру комнаты, армирующую сетку — по всей площади с нахлёстом.</p>'''
    how += schemes.screed_section()
    norms = (table(["Смесь", "Расход на 1 мм", "При толщине 50 мм"],
                   [["ЦПС М150", "≈ 2 кг/м²", "≈ 100 кг/м²"], ["Пескобетон М300", "≈ 2,2 кг/м²", "≈ 110 кг/м²"],
                    ["Наливной пол", "1,5–1,8 кг/м²", "заливают до 100 мм"]])
             + table(["На 1 м³ раствора", "1 : 3 (М150)", "1 : 4 (М100)"],
                     [["Цемент М500", "≈ 423 кг", "≈ 338 кг"], ["Песок", "≈ 0,98 м³", "≈ 1,04 м³"]]))
    calc_page("styazhka.html",
              "Калькулятор стяжки пола — сколько смеси или цемента и песка нужно",
              "Калькулятор стяжки пола: расчёт мешков сухой смеси, цемента и песка по площади и толщине, фиброволокно, демпферная лента и армирующая сетка.",
              "Калькулятор стяжки пола",
              "screed", "Купить смесь для стяжки", "Схема пола", inputs, how, norms,
              [("Какой толщины делать стяжку?", "Цементно-песчаная стяжка по плите — от 30 мм, по утеплителю или разделительному слою — от 40 мм. Для тонкого выравнивания до 10–30 мм используют наливной пол."),
               ("Что выгоднее — готовая смесь или цемент с песком?", "Цемент с песком дешевле в 1,5–2 раза, но требуют точной дозировки и бетономешалки. Готовая смесь удобнее на небольших площадях."),
               ("Сколько мешков ЦПС нужно на 1 м² стяжки толщиной 5 см?", "Около 100 кг, то есть 2,5 мешка по 40 кг."),
               ("Когда можно ходить по стяжке?", "Обычно через 2–3 дня, а класть ламинат или плитку — после полного высыхания: около недели на каждый сантиметр толщины для цементной стяжки.")])


def build_brick():
    bricks = [("65", "Одинарный 250×120×65"), ("88", "Полуторный 250×120×88"), ("138", "Двойной 250×120×138")]
    walls = [("0.5", "В полкирпича (120 мм)"), ("1", "В кирпич (250 мм)"), ("1.5", "В 1,5 кирпича (380 мм)"), ("2", "В 2 кирпича (510 мм)")]
    inputs = (h3("Что кладём") + seg("mode", [("perimeter", "Стены по периметру"), ("one", "Одна стена")], "perimeter")
              + h3("Размеры") + PRESET_CHIPS + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3", show="mode:perimeter"),
                                     field("room_h", "Высота, м", "2.7"))
              + openings()
              + h3("Кирпич и кладка") + grid(select("brick", "Кирпич", bricks, "65"), select("wall", "Толщина стены", walls, "1"),
                                             field("joint", "Шов, мм", "10"))
              + reserve([("3", "минимум"), ("5", "на бой"), ("10", "лицевой кирпич")], "5", "Запас на бой")
              + grid(price("Цена кирпича, ₽"), top=True))
    how = '''<p>Площадь кладки — длина стен × высота минус окна и двери. На 1 м² стены в полкирпича уходит 1 / ((0,25 + шов) × (высота кирпича + шов)) кирпичей; стена в кирпич — вдвое больше, в полтора — втрое. Итог увеличивается на запас на бой и округляется вверх.</p>
<p>Раствор = объём кладки минус объём самих кирпичей. Для раствора М100 (1 : 4) на 1 м³ берут около 338 кг цемента М500 и 1,04 м³ песка.</p>'''

    def per_m2(h, k):
        return 2 * k / ((0.25 + 0.01) * (h / 1000 + 0.01))
    rows = [[t.split(" ")[0]] + [ru(per_m2(int(h), k)) for k in (0.5, 1, 1.5, 2)] for h, t in bricks]
    norms = (table(["Кирпич, шов 10 мм", "В полкирпича", "В кирпич", "В 1,5 кирпича", "В 2 кирпича"], rows)
             + "\n<p>Количество кирпичей на 1 м² стены. Раствора на 1 м³ кладки из одинарного кирпича уходит около 0,2–0,24 м³.</p>")
    calc_page("kirpich.html",
              "Калькулятор кирпича — сколько кирпича и раствора нужно на стену",
              "Калькулятор кирпича онлайн: количество одинарного, полуторного или двойного кирпича на стену или дом, объём раствора, цемент и песок с учётом проёмов.",
              "Калькулятор кирпича",
              "brick", "Купить кирпич и цемент", "План стен", inputs, how, norms,
              [("Сколько кирпича в 1 м² кладки?", "Одинарного с учётом швов: 51 шт. в полкирпича и 103 шт. в кирпич. Полуторного — 39 и 78, двойного — 26 и 52."),
               ("Сколько нужно раствора на кладку?", "Раствор занимает около 20–24% объёма кладки: на 1 м³ стены из одинарного кирпича (≈ 394 шт. с учётом швов) уходит 0,2–0,24 м³ раствора."),
               ("Какой запас кирпича брать?", "5% на бой при перевозке и подрезке. Лицевой кирпич лучше брать из одной партии с запасом 5–10%: оттенок разных партий отличается."),
               ("Как учитывать окна и двери?", "Добавьте проёмы в калькулятор — их площадь вычтется из площади кладки. Перемычки над проёмами в расчёт не входят.")])


# ---------- статьи ----------

def article_card(a):
    fn, title, desc, _, human = a
    return (f'<a class="post-card" href="{fn}"><span class="eyebrow">Статья · {human}</span>'
            f'<span class="post-title">{title}</span><span class="post-desc">{desc}</span>'
            f'<span class="post-go">Читать →</span></a>')


def shop_config():
    """Партнёрские ссылки и данные рекламодателя — из того же assets/partners.js, что у калькуляторов."""
    with open(os.path.join(ROOT, "assets", "partners.js"), encoding="utf-8") as f:
        js = f.read()
    links = dict(re.findall(r'^\s+([A-Z_]+): "(https://[^"]+)"', js, re.M))
    def get(key):
        return re.search(r'\b' + key + r': "([^"]+)"', js).group(1)
    return links, get("button"), get("advertiser"), get("inn"), get("id")


def buy_static(title, lead, main, extras):
    """Блок «Купить …» для статей: та же разметка, что строит calc.js на калькуляторах."""
    links, button, advertiser, inn, shop_id = shop_config()
    def link(key, text, cls):
        return (f'<a class="{cls}" href="{html.escape(links[key])}" target="_blank" rel="sponsored nofollow noopener"'
                f' data-aff="{key}" data-shop="{shop_id}">{text}</a>')
    keys = [main] + [k for k, _ in extras]
    erids = []
    for k in keys:
        e = parse_qs(urlparse(links[k]).query).get("erid", [""])[0]
        if e and e not in erids:
            erids.append(e)
    small = "".join(link(k, t, "buy-small") for k, t in extras)
    return (f'<section class="buy-card"><h2>{title}</h2><p class="buy-lead">{lead}</p>'
            f'<div class="buy-actions">{link(main, button, "buy-btn")}'
            + (f'<div class="buy-extra">{small}</div>' if small else "")
            + f'</div><p class="ad-mark">Реклама. {advertiser}, ИНН {inn}, erid: {", ".join(erids)}</p></section>')


# Те же формулы, что в assets/calc.js (калькулятор плитки): округление вверх с допуском.
def up(x):
    return math.ceil(x - 1e-7)


def up1(x):
    return up(x * 10) / 10


def tile_calc(area, a, b, reserve=10, per_pack=0, joint=2, thick=8):
    count = up(area / ((a / 100) * (b / 100)) * (1 + reserve / 100))
    packs = up(count / per_pack) if per_pack else 0
    side = max(a, b)
    glue = up(area * (3.5 if side <= 20 else 4.5 if side <= 40 else 6))
    grout = up1(((a * 10 + b * 10) / (a * 10 * b * 10)) * thick * joint * 1.6 * area * 1.1)
    return count, packs, glue, grout


def ru_num(x, digits=1):
    s = f"{x:.{digits}f}".rstrip("0").rstrip(".") if digits else str(int(x))
    return s.replace(".", ",")


def plitka_link(surface, L, W, H, a, b, per_pack, door=True):
    q = {"surface": surface, "room_l": L, "room_w": W, "room_h": H, "tile_w": a, "tile_h": b,
         "per_pack": per_pack, "joint": 2, "thickness": 8, "reserve": 10, "price": "",
         "o": "d:0.7x2x1" if door else ""}
    return "plitka.html?" + html.escape(urlencode(q))


def build_stati():
    cards = "".join(article_card(a) for a in ARTICLES)
    main = f"""<main class="wrap calc-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><span>Статьи</span></nav>
<div class="calc-head"><h1>Статьи</h1><span class="calc-tagline">Готовые расчёты материалов для ремонта</span></div>
<p class="page-lead">Разбираем типовые ремонты на цифрах: сколько материала брать, как измерить комнату и где чаще всего ошибаются. Все расчёты сделаны теми же формулами, что в калькуляторах сайта.</p>
<div class="posts">{cards}</div>
</main>"""
    page("stati.html", "Статьи о ремонте: готовые расчёты материалов — Метраж",
         "Статьи о ремонте с готовыми расчётами: сколько плитки, обоев, краски и других материалов нужно на комнату, как измерить помещение и сколько брать запаса.",
         main, crumb="Статьи", app=False, lastmod=ARTICLES[0][3][:10], og_title="Статьи о ремонте")


def build_article_tiles():
    fn, h1, card_desc, iso, human = ARTICLES[0]
    H, door = 2.5, 0.7 * 2.0
    rows_tiles, rows_mix, results = [], [], {}
    for L, W in [(2, 2), (2, 3), (3, 3)]:
        floor = L * W
        walls = 2 * (L + W) * H - door
        f_cnt, f_pk, f_glue, f_grout = tile_calc(floor, 30, 30, per_pack=11)
        w_cnt, w_pk, w_glue, w_grout = tile_calc(walls, 25, 40, per_pack=15)
        results[(L, W)] = (floor, f_cnt, walls, w_cnt)
        name = f"{L}×{W} м"
        links = (f'<a href="{plitka_link("floor", L, W, H, 30, 30, 11, door=False)}">пол</a> · '
                 f'<a href="{plitka_link("walls", L, W, H, 25, 40, 15)}">стены</a>')
        rows_tiles.append([f"<b>{name}</b>", ru_num(floor), f"<b>{f_cnt}</b>", f_pk, ru_num(walls), f"<b>{w_cnt}</b>", w_pk, links])
        total_glue = f_glue + w_glue
        rows_mix.append([f"<b>{name}</b>", f"{f_glue} кг", f"{w_glue} кг", f"{total_glue} кг ({up(total_glue / 25)} меш. по 25 кг)",
                         f"{ru_num(f_grout)} кг", f"{ru_num(w_grout)} кг"])
    f22, f22pk = tile_calc(4, 30, 30, per_pack=11)[:2]
    w22 = results[(2, 2)][3]
    # Пример «не до потолка»: ванная 2×2, плитка до 1,5 м, дверь закрывает 0,7×1,5 м этой полосы.
    low_area = 2 * (2 + 2) * 1.5 - 0.7 * 1.5
    low_cnt = tile_calc(low_area, 25, 40)[0]
    ex_walls = results[(2, 3)][2]
    btn = lambda href, text="Посчитать для своей ванной": f'<p class="cta"><a class="btn-primary" href="{href}">{text}</a></p>'

    faq = [
        ("Сколько плитки нужно на пол ванной 4 м²?",
         f"Пол 2×2 м — это 4 м². При плитке 30×30 см и запасе 10% нужно {f22} плиток: 4 / 0,09 × 1,1 = 48,9, округляем вверх. При фасовке по 11 штук это {f22pk} упаковок."),
        ("Почему плиток нужно больше, чем площадь, делённая на площадь плитки?",
         "Крайние плитки у стен и вокруг двери подрезают, обрезки редко удаётся использовать, а часть плитки бьётся при резке. Поэтому к расчёту добавляют запас 10–20%, а результат округляют вверх до целой плитки и целой упаковки."),
        ("Нужно ли класть плитку под ванной?",
         "Это решают до покупки. Если пол под ванной плиткой не закрывают, вычтите площадь ванны из площади пола: например, ванна 1,7×0,7 м уменьшает пол на 1,19 м²."),
        ("Сколько клея нужно на ванную 2×2 м?",
         f"По норме калькулятора для плитки 20–40 см — около 4,5 кг на м². На пол 4 м² — {tile_calc(4, 30, 30)[2]} кг, на стены 18,6 м² — {tile_calc(18.6, 25, 40)[2]} кг, всего {tile_calc(4, 30, 30)[2] + tile_calc(18.6, 25, 40)[2]} кг, то есть {up((tile_calc(4, 30, 30)[2] + tile_calc(18.6, 25, 40)[2]) / 25)} мешков по 25 кг. Точный расход зависит от ровности основания и указан на мешке."),
    ]
    tiles_table = table(["Ванная", "Пол, м²", "Плитка 30×30, шт.", "Упаковок по 11", "Стены, м²", "Плитка 25×40, шт.", "Упаковок по 15", "Открыть в калькуляторе"], rows_tiles)
    mix_table = table(["Ванная", "Клей на пол", "Клей на стены", "Клей всего", "Затирка на пол", "Затирка на стены"], rows_mix)
    reserve_table = table(["Укладка", "Запас", "Почему"],
                          [["Прямая, плитка по сетке", "10%", "подрезка у стен и вокруг двери, бой при резке"],
                           ["Диагональная", "15%", "по всем стенам режутся треугольники, обрезков больше"],
                           ["Сложная: ёлочка, модульная, крупный формат", "20%", "много подрезки и риск сколов"]])
    buy = buy_static("Купить плитку, клей и затирку",
                     "Плитку, клей и затирку можно выбрать в одном магазине — так проще собрать всё к началу работ.",
                     "PLITKA", [("KLEY_PLITOCHNY", "Клей для плитки"), ("ZATIRKA", "Затирка")])

    main = f"""<main class="wrap calc-page article-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><a href="stati.html">Статьи</a><span aria-hidden="true">→</span><span>Сколько плитки нужно на ванную</span></nav>
<article class="article post">
<header class="post-head">
<h1>{h1}</h1>
<p class="post-meta"><time datetime="{iso}">{human}</time> · Метраж</p>
</header>
<p class="post-lead">Для пола ванной 2×2 м нужно <b>{f22} плиток 30×30</b> с запасом 10%: площадь пола 4 м² делим на площадь плитки 0,09 м², прибавляем 10% и округляем вверх. Для стен той же ванной при высоте 2,5 м — <b>{w22} плиток 25×40</b>. Ниже — готовые расчёты для трёх типовых размеров, клей и затирка, а также как пересчитать всё под свою ванную.</p>
{btn(plitka_link("both", 2, 2, H, 30, 30, 11))}

<h2>Готовые расчёты для ванной 2×2, 2×3 и 3×3 м</h2>
<p>Условия для всех трёх вариантов:</p>
<ul>
<li>высота стен — 2,5 м, плитка от пола до потолка;</li>
<li>дверь 0,7×2,0 м — её площадь 1,4 м² вычитаем из стен;</li>
<li>пол — плитка 30×30 см, стены — 25×40 см;</li>
<li>запас — 10%, прямая укладка;</li>
<li>фасовка: 30×30 — по 11 штук в упаковке (0,99 м²), 25×40 — по 15 штук (1,5 м²).</li>
</ul>
{tiles_table}
<p>Фасовка у производителей отличается, поэтому число упаковок пересчитайте по своей коробке: оно указано на торце вместе с площадью. Ссылки «пол» и «стены» в последнем столбце открывают калькулятор с уже подставленными размерами — останется поменять то, что отличается у вас.</p>

<h3>Клей и затирка</h3>
{mix_table}
<p>Клей считаем по норме калькулятора: для плитки со стороной от 20 до 40 см — 4,5 кг на м², на площадь без запаса. Затирку — по формуле производителей: (A + B) / (A × B) × толщина плитки × ширина шва × 1,6 кг/м² плюс 10%. Здесь взяты шов 2 мм и толщина плитки 8 мм. Если шов шире, затирки понадобится пропорционально больше.</p>

<h3>Как получены цифры</h3>
<p>Площадь пола — длина × ширина. Площадь стен — периметр × высота минус дверь. Например, для ванной 2×3 м: 2 × (2 + 3) × 2,5 = 25 м², минус дверь 1,4 м² — остаётся {ru_num(ex_walls)} м². Плитка 25×40 занимает 0,1 м², значит нужно {ru_num(ex_walls)} / 0,1 × 1,1 = 259,6, то есть 260 плиток. Результат всегда округляется вверх: 259 плиток не хватит.</p>

<h2>Как измерить ванную</h2>
<ol>
<li>Измерьте длину и ширину комнаты у пола и на высоте около 1,5 м. Стены редко бывают идеально ровными — берите большее значение.</li>
<li>Измерьте высоту, до которой будет плитка: до потолка или до выбранного уровня.</li>
<li>Измерьте дверной проём — ширину и высоту.</li>
<li>Отдельно запишите размеры ванны или душевого поддона, короба и ниш.</li>
<li>Все размеры переводите в метры с точностью до сантиметра: 1 м 72 см — это 1,72 м.</li>
</ol>
{schemes.bath_measure()}

<h2>Что вычитать: дверь, ванну и короб</h2>
<ul>
<li><b>Дверь.</b> Вычитайте площадь проёма: ширина × высота. В калькуляторе дверь добавляется кнопкой «Добавить проём».</li>
<li><b>Ванна.</b> Если стену за ванной ниже борта плиткой не закрывают, вычтите эту полосу: длина ванны × высота борта. В калькуляторе её удобно добавить как ещё один проём. Если не кладёте плитку на пол под ванной, вычтите и её площадь из пола.</li>
<li><b>Экран под ванной.</b> Если экран облицовывают плиткой, наоборот, прибавьте его площадь: длина × высота.</li>
<li><b>Короб для труб.</b> Короб не уменьшает, а увеличивает площадь облицовки: прибавьте площадь всех его видимых граней.</li>
</ul>
<p>Окна в ванной редки, но если окно есть, его площадь тоже вычитается, а откосы прибавляются.</p>
{btn(plitka_link("walls", 2, 3, H, 25, 40, 15), "Посчитать стены своей ванной")}

<h2>Сколько брать запаса</h2>
{reserve_table}
{schemes.tile_layouts()}
<p>Запас нужен не только на подрезку. Плитку выпускают партиями, и у разных партий немного отличается оттенок и калибр — точный размер. Если через месяц не хватит двух плиток, той же партии в магазине может уже не быть. Поэтому всю плитку берут сразу и из одной партии: номер партии, тон и калибр указаны на коробке. После ремонта стоит оставить 2–3 целые плитки на случай замены.</p>

<h2>Если стены облицовываются не до потолка</h2>
<p>Тогда вместо высоты комнаты подставьте высоту укладки, а у двери учитывайте только ту часть проёма, что попадает в эту полосу. Пример: ванная 2×2 м, плитка до высоты 1,5 м. Стены: 2 × (2 + 2) × 1,5 = 12 м², минус часть двери 0,7 × 1,5 = 1,05 м², остаётся {ru_num(low_area, 2)} м². Плиток 25×40 с запасом 10% понадобится {low_cnt}. Стену выше плитки обычно красят — её можно посчитать в <a href="kraska.html">калькуляторе краски</a>.</p>

<h2>Частые ошибки при покупке</h2>
<ul>
<li><b>Покупка впритык.</b> Без запаса плитки почти всегда не хватает: часть уходит на подрезку и в бой даже в простой комнате.</li>
<li><b>Разные партии.</b> Плитка из двух партий может заметно отличаться оттенком на одной стене. Сверяйте номер партии на всех коробках.</li>
<li><b>Счёт в квадратных метрах вместо штук и упаковок.</b> Магазин продаёт плитку упаковками, поэтому итог нужно округлить вверх до целой упаковки.</li>
<li><b>Стены по площади пола.</b> Площадь стен ванной в 3–5 раз больше площади пола: у ванной 2×2 м это 4 м² пола и {ru_num(results[(2, 2)][2])} м² стен.</li>
<li><b>Забытые клей и затирка.</b> Их покупают вместе с плиткой — цифры для типовых ванных есть в таблице выше.</li>
</ul>

{buy}
{btn(plitka_link("both", 3, 3, H, 30, 30, 11))}
{faq_html(faq)}
</article>
</main>"""

    article_ld = {"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": card_desc,
                  "datePublished": iso, "dateModified": iso, "inLanguage": "ru",
                  "mainEntityOfPage": SITE_URL + fn,
                  "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
                  "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL}}
    page(fn, "Сколько плитки нужно на ванную: расчёт для 2×2, 2×3 и 3×3 м — Метраж",
         "Сколько плитки нужно на ванную: готовая таблица для пола и стен ванных 2×2, 2×3 и 3×3 м — штуки, упаковки, клей и затирка. Как измерить ванную и сколько брать запаса.",
         main, faq, crumb="Сколько плитки нужно на ванную", trail=[("Статьи", "stati.html")],
         ld_extra=[article_ld], app=False, lastmod=iso[:10],
         og_title="Сколько плитки нужно на ванную", og_icon=ICONS["plitka"])
    return results


# ---------- хабы «Ремонт под ключ» ----------

# Этап: id, заголовок, что делается, какой материал, позиции. Позиция (item):
#   calc  — калькулятор (тип из assets/calc.js), его значения по умолчанию берутся из CALC_DEFAULTS;
#   set   — что поменять относительно значений по умолчанию;
#   room  — "room" (размеры комнаты), "apron" (фартук: длина × высота) или "ext" (наружная стена);
#   ops   — проёмы: "all", "w" (только окна) или "none" (как в калькуляторе, где блок проёмов скрыт);
#   doors — подставить число и ширину дверей из проёмов (ламинат: плинтус и порожки);
#   row   — показать строку результата вместо главного числа; rows — дополнительные строки;
#   name  — название в списке покупок; buy — ключ партнёрской ссылки из assets/partners.js.
# when — этап показывается только при значении переключателя хаба, например {"finish": "paint"}.
def stage(sid, title, what, material, items, when=None):
    return {"id": sid, "title": title, "what": what, "material": material, "items": items, "when": when}


def item(calc, name, buy="", set=None, room="room", ops="all", doors=False, row=None, rows=()):
    return {"calc": calc, "name": name, "buy": buy, "set": set or {}, "room": room, "ops": ops,
            "doors": doors, "row": row, "rows": list(rows)}


TILE_GLUE = [item("tile", "Плиточный клей", "KLEY_PLITOCHNY", row="Плиточный клей"),
             item("tile", "Затирка", "ZATIRKA", row="Затирка")]


def glue_for(set, room="room", ops="all"):
    return [dict(i, set=set, room=room, ops=ops) for i in TILE_GLUE]


def hub_bath():
    tile_both = {"surface": "both"}
    stages = [
        stage("walls", "Выравнивание стен",
              "Стены выводят в плоскость по маякам: под плитку перепад не должен превышать 2 мм на 2 м. Перед штукатуркой стены грунтуют.",
              "штукатурка (в расчёте — гипсовая, средний слой 15 мм, мешки по 30 кг), маяки 3 м, грунтовка.",
              [item("plaster", "Штукатурка", "OSTALNOE", rows=["Маяки 3 м", "Грунтовка"])]),
        stage("screed", "Стяжка пола",
              "Пол выравнивают стяжкой по маякам, по периметру клеят демпферную ленту. Плитку кладут после полного высыхания стяжки.",
              "сухая смесь ЦПС М150, средняя толщина 50 мм, мешки по 40 кг; демпферная лента.",
              [item("screed", "Смесь для стяжки", "OSTALNOE", rows=["Демпферная лента"])]),
    ]
    if "selflevel" in CALC_DEFAULTS:
        stages.append(stage("selflevel", "Наливной пол",
                            "Тонкий слой наливного пола доводит стяжку до идеально ровной поверхности под плитку. Основание грунтуют, по периметру — демпферная лента.",
                            "финишная смесь наливного пола, слой 10 мм, мешки по 25 кг; грунтовка.",
                            [item("selflevel", "Наливной пол", "NALIVNOY_POL", rows=["Грунтовка"])]))
    stages += [
        stage("tile", "Плитка на стены и пол",
              "Сначала облицовывают стены — от второго ряда снизу вверх, затем пол и нижний ряд стен. Запас 10% уходит на подрезку и бой.",
              "плитка 30×60 см по 8 шт. в упаковке, запас 10%. Размер и фасовку своей плитки поменяйте в калькуляторе.",
              [item("tile", "Плитка", "PLITKA", set=tile_both, rows=["Площадь облицовки"])]),
        stage("glue", "Клей и затирка",
              "Клей наносят зубчатым шпателем, швы держат крестиками или СВП. Затирают швы через сутки, когда клей схватится.",
              "плиточный клей в мешках по 25 кг, затирка в упаковках по 2 кг, крестики или СВП.",
              glue_for(tile_both) + [item("tile", "Крестики / СВП", set=tile_both, row="Крестики / СВП")]),
        stage("ceiling", "Покраска потолка",
              "Потолок грунтуют и красят в два слоя влагостойкой краской — в ванной лучше латексной или акриловой с пометкой «для влажных помещений».",
              "краска (расход 9 м²/л на слой, два слоя, тара 9 л), грунтовка.",
              [item("paint", "Краска для потолка", "KRASKA", set={"surface": "ceiling"}, ops="none", rows=["Грунтовка (1 слой)"])]),
    ]
    return {
        "fn": "remont-vannoy.html", "type": "hub-bath", "short": "Ремонт ванной", "crumb": "Ремонт ванной",
        "h1": "Ремонт ванной: расчёт материалов",
        "title": "Ремонт ванной: расчёт материалов по этапам — Метраж",
        "desc": "Ремонт ванной под ключ: сколько штукатурки, смеси для стяжки, плитки, клея, затирки и краски нужно на ванную по вашим размерам. Все этапы на одной странице.",
        "lead": "Введите размеры ванной — и получите материалы на весь ремонт: от выравнивания стен до покраски потолка. Каждый этап считается тем же калькулятором, что на отдельной странице, с его значениями по умолчанию.",
        "card": "Штукатурка, стяжка, плитка, клей, потолок",
        "card_long": "Выравнивание стен, стяжка пола, плитка на стены и пол, клей и затирка, покраска потолка.",
        "room": ("2", "2", "2.5"), "openings": "d:0.7x2", "toggles": "",
        "stages": stages, "icon": ICONS["plitka"],
        "buy": ("Купить материалы для ванной", "Плитку, клей, затирку, смеси и краску можно собрать в одном магазине.",
                "PLITKA", [("KLEY_PLITOCHNY", "Клей для плитки"), ("ZATIRKA", "Затирка"), ("OSTALNOE", "Штукатурка и стяжка"), ("KRASKA", "Краска")]),
        "article": True,
        "faq": [("С чего начинать ремонт ванной?", "С демонтажа и сантехники: трубы и выводы под смесители разводят до выравнивания стен. Дальше по порядку — штукатурка, стяжка, гидроизоляция, плитка и потолок."),
                ("Какой запас плитки брать на ванную?", "10% при прямой укладке и 15% при диагональной. Плитку берут сразу и из одной партии: тон и калибр у разных партий отличаются."),
                ("Нужно ли штукатурить стены под плитку?", "Если перепад больше 3–5 мм на 2 м — да. Плиточным клеем можно выровнять 1–3 мм, но толстый слой клея дороже штукатурки и дольше сохнет."),
                ("Почему результат отличается от моих расчётов?", "Хаб использует значения калькуляторов по умолчанию: плитку 30×60, слой штукатурки 15 мм, стяжку 50 мм. Нажмите «Уточнить в калькуляторе» и введите свои параметры.")],
    }


def hub_kitchen():
    floor = {"surface": "floor"}
    stages = [
        stage("walls", "Штукатурка и шпаклёвка стен",
              "Стены выравнивают штукатуркой по маякам, затем шпаклюют: стартовый слой убирает мелкие неровности, финишный готовит стену под покраску или обои.",
              "штукатурка (гипсовая, слой 15 мм, мешки по 30 кг), шпаклёвка стартовая 2 мм и финишная 1 мм, грунтовка.",
              [item("plaster", "Штукатурка", "OSTALNOE", rows=["Маяки 3 м"]),
               item("putty", "Шпаклёвка", "OSTALNOE", rows=["Стартовая шпаклёвка", "Финишная шпаклёвка"])]),
        stage("apron", "Плитка на фартук",
              "Фартук — полоса плитки между столешницей и навесными шкафами. Обычно 0,6 м в высоту по длине рабочей зоны. Размеры фартука задайте в форме.",
              "плитка 30×60 см по 8 шт. в упаковке, запас 10%, плиточный клей, затирка.",
              [item("tile", "Плитка для фартука", "PLITKA", set=floor, room="apron", ops="none", rows=["Площадь облицовки"])]
              + glue_for(floor, room="apron", ops="none")),
        stage("paint", "Покраска стен",
              "Стены грунтуют и красят в два слоя. Для кухни берите моющуюся краску: её можно протирать от брызг и жира.",
              "краска (расход 9 м²/л на слой, два слоя, тара 9 л), грунтовка, малярный скотч.",
              [item("paint", "Краска для стен", "KRASKA", rows=["Грунтовка (1 слой)"])], when={"finish": "paint"}),
        stage("wallpaper", "Обои",
              "Обои клеят встык после шпаклёвки и грунтовки. На кухне практичнее моющиеся флизелиновые или виниловые.",
              "обои 1,06 × 10,05 м без подгонки рисунка, обойный клей.",
              [item("wallpaper", "Обои", "OBOI", rows=["Обойный клей"])], when={"finish": "wallpaper"}),
        stage("laminate", "Ламинат на пол",
              "Ламинат кладут на ровное сухое основание по подложке, вдоль света из окна. У стен оставляют зазор 8–10 мм под плинтус.",
              "ламинат по 2,131 м² в упаковке, запас 7%, подложка, плинтус.",
              [item("laminate", "Ламинат", "LAMINAT", doors=True, rows=["Подложка", "Плинтус"])], when={"floor": "laminate"}),
        stage("floortile", "Плитка на пол",
              "Плитку на пол кухни кладут от центра или от видимого угла, подрезку уводят под мебель.",
              "плитка 30×60 см по 8 шт. в упаковке, запас 10%, плиточный клей, затирка.",
              [item("tile", "Плитка для пола", "PLITKA", set=floor, ops="none", rows=["Площадь облицовки"])]
              + glue_for(floor, ops="none"), when={"floor": "tile"}),
    ]
    toggles = (h3("Отделка") + '<div class="hub-toggles">'
               + '<div><span class="toggle-cap">Стены</span>' + seg("finish", [("paint", "Покраска"), ("wallpaper", "Обои")], "paint") + "</div>"
               + '<div><span class="toggle-cap">Пол</span>' + seg("floor", [("laminate", "Ламинат"), ("tile", "Плитка")], "laminate") + "</div></div>"
               + h3("Фартук") + grid(field("apron_l", "Длина, м", "2.5"), field("apron_h", "Высота, м", "0.6"), cols=2))
    return {
        "fn": "remont-kuhni.html", "type": "hub-kitchen", "short": "Ремонт кухни", "crumb": "Ремонт кухни",
        "h1": "Ремонт кухни: расчёт материалов",
        "title": "Ремонт кухни: расчёт материалов по этапам — Метраж",
        "desc": "Ремонт кухни под ключ: штукатурка и шпаклёвка стен, плитка на фартук, краска или обои, ламинат или плитка на пол — сколько материала нужно по вашим размерам.",
        "lead": "Введите размеры кухни, выберите отделку стен и пола — и получите материалы на весь ремонт. Каждый этап считается тем же калькулятором, что на отдельной странице, с его значениями по умолчанию.",
        "card": "Стены, фартук, краска или обои, пол",
        "card_long": "Штукатурка и шпаклёвка стен, плитка на фартук, покраска или обои, ламинат или плитка на пол.",
        "room": ("3", "3", "2.5"), "openings": "d:0.8x2;w:1.5x1.5", "toggles": toggles,
        "stages": stages, "icon": ICONS["kraska"],
        "buy": ("Купить материалы для кухни", "Плитку для фартука, краску, обои и ламинат можно выбрать в одном магазине.",
                "PLITKA", [("KLEY_PLITOCHNY", "Клей для плитки"), ("KRASKA", "Краска"), ("OBOI", "Обои"), ("LAMINAT", "Ламинат")]),
        "article": True,
        "faq": [("Какого размера делать фартук на кухне?", "Стандартная высота — 0,6 м: от столешницы на высоте 0,85–0,9 м до навесных шкафов. Длина — вся рабочая зона, обычно 2–3 м. Если над плитой нет шкафа, фартук там поднимают до вытяжки."),
                ("Что лучше на кухне — краска или обои?", "Моющаяся краска практичнее у плиты и мойки: её можно протирать. Обои подходят для обеденной зоны. Переключатель «Стены» пересчитывает этап."),
                ("Ламинат или плитка на пол кухни?", "Плитка не боится воды и подходит к тёплому полу. Влагостойкий ламинат теплее на ощупь и дешевле в укладке. Переключатель «Пол» пересчитывает этап."),
                ("Нужно ли красить стену за фартуком?", "Нет. В этой версии расчёта площадь стен для краски и обоев считается без вычета фартука — это небольшой запас. Точнее можно посчитать в калькуляторе краски.")],
    }


def hub_room():
    stages = [
        stage("insulation", "Утепление наружной стены",
              "Если у комнаты есть наружная стена, её утепляют первой — до шпаклёвки. Утеплитель закрывают пароизоляцией и обшивают, например, гипсокартоном.",
              "утеплитель — плиты 1200×600×50 мм, толщина утепления 100 мм; пароизоляция, дюбели-грибки.",
              [item("insulation", "Утеплитель", "OSTALNOE", set={"surface": "one"}, room="ext", ops="w",
                    rows=["Пароизоляция (нахлёст 10 см)", "Дюбели-грибки"])], when={"ext": "yes"}),
        stage("putty", "Шпаклёвка стен",
              "Стартовая шпаклёвка убирает неровности до 5 мм, финишная делает стену гладкой. Перед каждым слоем — грунтовка.",
              "шпаклёвка стартовая 2 мм (мешки по 25 кг) и финишная 1 мм (по 20 кг), грунтовка, абразивная сетка.",
              [item("putty", "Шпаклёвка", "OSTALNOE", rows=["Стартовая шпаклёвка", "Финишная шпаклёвка"])]),
        stage("wallpaper", "Обои",
              "Обои клеят после шпаклёвки и грунтовки, от окна. Рулоны берут из одной партии и с запасом в один рулон.",
              "обои 1,06 × 10,05 м без подгонки рисунка, обойный клей.",
              [item("wallpaper", "Обои", "OBOI", rows=["Обойный клей"])], when={"finish": "wallpaper"}),
        stage("paint", "Покраска стен",
              "Стены грунтуют и красят в два слоя валиком, углы — кистью.",
              "краска (расход 9 м²/л на слой, два слоя, тара 9 л), грунтовка, малярный скотч.",
              [item("paint", "Краска для стен", "KRASKA", rows=["Грунтовка (1 слой)"])], when={"finish": "paint"}),
        stage("laminate", "Ламинат",
              "Ламинат кладут по подложке на ровное сухое основание, вдоль света из окна, с зазором 8–10 мм у стен.",
              "ламинат по 2,131 м² в упаковке, запас 7%, подложка 10 м² в рулоне.",
              [item("laminate", "Ламинат", "LAMINAT", doors=True, rows=["Подложка"])]),
        stage("plinth", "Плинтус",
              "Плинтус ставят последним: он закрывает зазор у стен. Длина — периметр комнаты минус ширина дверей.",
              "плинтус по 2,5 м, внутренние углы и заглушки у дверей.",
              [item("laminate", "Плинтус", "LAMINAT", doors=True, row="Плинтус", rows=["Углы плинтуса (внутр.)", "Заглушки плинтуса"])]),
    ]
    toggles = (h3("Отделка") + '<div class="hub-toggles">'
               + '<div><span class="toggle-cap">Стены</span>' + seg("finish", [("wallpaper", "Обои"), ("paint", "Покраска")], "wallpaper") + "</div>"
               + '<div><span class="toggle-cap">Наружная стена</span>' + seg("ext", [("no", "Нет"), ("yes", "Есть")], "no") + "</div></div>"
               + grid(field("ext_l", "Длина наружной стены, м", "3", show="ext:yes"), top=True)
               + '<p class="hint" data-show="ext:yes">Утепление считается для одной наружной стены за вычетом окон.</p>')
    return {
        "fn": "remont-komnaty.html", "type": "hub-room", "short": "Ремонт комнаты", "crumb": "Ремонт комнаты",
        "h1": "Ремонт комнаты: расчёт материалов",
        "title": "Ремонт комнаты: расчёт материалов по этапам — Метраж",
        "desc": "Ремонт комнаты под ключ: шпаклёвка, обои или краска, ламинат, плинтус и утеплитель для наружной стены — сколько материала нужно по вашим размерам.",
        "lead": "Введите размеры комнаты, выберите обои или покраску и отметьте наружную стену — и получите материалы на весь ремонт. Каждый этап считается тем же калькулятором, что на отдельной странице, с его значениями по умолчанию.",
        "card": "Шпаклёвка, обои или краска, ламинат",
        "card_long": "Утепление наружной стены, шпаклёвка, обои или покраска, ламинат и плинтус.",
        "room": ("3", "4", "2.5"), "openings": "d:0.8x2;w:1.5x1.5", "toggles": toggles,
        "stages": stages, "icon": ICONS["oboi"],
        "buy": ("Купить материалы для комнаты", "Обои, краску, ламинат и смеси можно выбрать в одном магазине.",
                "LAMINAT", [("OBOI", "Обои"), ("KRASKA", "Краска"), ("OSTALNOE", "Шпаклёвка и утеплитель")]),
        "article": False,
        "faq": [("В каком порядке делать ремонт комнаты?", "Сверху вниз и от грязных работ к чистым: утепление и электрика, выравнивание стен, шпаклёвка, потолок, обои или покраска, пол, плинтус."),
                ("Сколько обоев нужно на комнату 3×4 м?", "При высоте 2,5 м, двери 0,8×2 м и окне 1,5×1,5 м — около 4 рулонов метровых обоев без подгонки рисунка. Точнее — по кнопке «Уточнить в калькуляторе»."),
                ("Нужно ли утеплять наружную стену изнутри?", "Только если стена промерзает и утеплить её снаружи нельзя. Изнутри обязательно кладут пароизоляцию, иначе в утеплителе будет конденсат."),
                ("Почему плинтуса меньше, чем периметр комнаты?", "Из периметра вычитается ширина дверей: в проёме плинтус не ставят. К длине добавляется 5% на подрезку в углах.")],
    }


def hub_stage_html(i, st):
    hidden = ""
    if st["when"]:
        (k, v), = st["when"].items()
        hidden = f' data-when="{k}:{v}"'
    return (f'<li class="stage" id="st-{st["id"]}" data-stage="{i}"{hidden}>'
            f'<h2 class="stage-title">{st["title"]}</h2>'
            f'<p class="stage-what">{st["what"]}</p>'
            f'<p class="stage-mat"><b>Материал:</b> {st["material"]}</p>'
            f'<div class="stage-res" aria-live="polite"><noscript><p>Для расчёта по этапам нужен JavaScript. Откройте калькуляторы по ссылкам в меню.</p></noscript></div>'
            f'<button type="button" class="stage-add" data-act="hub-stage" data-stage="{i}">Добавить этап в список покупок</button></li>')


def hub_data(h):
    """Данные для assets/hub.js: значения калькуляторов по умолчанию, страницы калькуляторов, этапы."""
    calcs = sorted({it["calc"] for st in h["stages"] for it in st["items"]})
    return {"title": h["short"],
            "defaults": {c: CALC_DEFAULTS[c] for c in calcs},
            "pages": {c: CALC_PAGES[c] for c in calcs},
            "openings": sorted(c for c in calcs if c in CALC_OPENINGS),
            "stages": [{"id": st["id"], "title": st["title"], "when": st["when"], "items": st["items"]} for st in h["stages"]]}


HUBS = []


def build_hub(h):
    L, W, H = h["room"]
    form = (h3("Помещение") + PRESET_CHIPS + grid(field("room_l", "Длина, м", L), field("room_w", "Ширина, м", W), field("room_h", "Высота, м", H))
            + openings() + h["toggles"])
    stages = "".join(hub_stage_html(i, st) for i, st in enumerate(h["stages"]))
    data = json.dumps(hub_data(h), ensure_ascii=False).replace("</", "<\\/")
    related = ('<h2>По теме</h2>\n<div class="posts">' + article_card(ARTICLES[0]) + "</div>") if h["article"] else ""
    others = "".join(f'<a href="{o["fn"]}">{o["short"]} →</a>' for o in HUBS if o["fn"] != h["fn"])
    main = f'''<main class="wrap calc-page hub-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><a href="remont.html">Ремонт под ключ</a><span aria-hidden="true">→</span><span>{h["crumb"]}</span></nav>
<div class="calc-head"><h1>{h["h1"]}</h1><span class="calc-tagline">Все этапы по вашим размерам</span></div>
<p class="page-lead">{h["lead"]}</p>
<div class="calc hub">
<form class="form-card hub-form" id="calc-form" data-calc="{h["type"]}" data-openings="{h["openings"]}" autocomplete="off" novalidate aria-label="Размеры помещения">
{form}
</form>
<section class="hub-stages" id="result" aria-label="Этапы ремонта">
<ol class="stages">{stages}</ol>
<div class="hub-actions"><button type="button" class="btn-primary" data-act="hub-all">Добавить всё в список покупок</button>
<button type="button" class="list-btn" data-act="share">Поделиться</button><button type="button" class="list-btn" data-act="print">Распечатать</button></div>
<p class="hint">Расчёты ориентировочные: этапы считаются с параметрами калькуляторов по умолчанию. Свою плитку, смесь или толщину слоя задайте по ссылке «Уточнить в калькуляторе».</p>
<div data-fb-slot></div>
</section>
</div>
<script type="application/json" id="hub-data">{data}</script>
{buy_static(*h["buy"])}
{AD_SLOT}
<article class="article">
{faq_html(h["faq"])}
{related}
<p class="hub-others">{others}<a href="remont.html">Все хабы «Ремонт под ключ»</a></p>
</article>
</main>'''
    page(h["fn"], h["title"], h["desc"], main, h["faq"], crumb=h["crumb"], trail=[("Ремонт под ключ", "remont.html")],
         app=False, lastmod="2026-10-29", og_title=h["h1"], og_icon=h["icon"],
         scripts='\n<script src="assets/hub.js"></script>\n<script src="assets/calc.js"></script>')


def hub_card(h):
    return f'<a class="card hub-card" href="{h["fn"]}">{h["icon"]}<span class="card-name">{h["short"]}</span><span class="card-desc">{h["card"]}</span></a>'


def build_hubs():
    HUBS[:] = [hub_bath(), hub_kitchen(), hub_room()]
    for h in HUBS:
        build_hub(h)
    cards = "".join(
        f'<a class="post-card hub-post" href="{h["fn"]}"><span class="eyebrow">Ремонт под ключ</span>'
        f'<span class="post-title">{h["short"]}</span>'
        f'<span class="post-desc">{h["card_long"]}</span>'
        f'<span class="post-go">Рассчитать →</span></a>' for h in HUBS)
    main = f"""<main class="wrap calc-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><span>Ремонт под ключ</span></nav>
<div class="calc-head"><h1>Ремонт под ключ: расчёт материалов</h1><span class="calc-tagline">Все этапы на одной странице</span></div>
<p class="page-lead">Выберите помещение, введите его размеры — и получите материалы на весь ремонт по этапам: что делается, какой материал нужен и сколько его купить. Каждый этап можно уточнить в отдельном калькуляторе, а весь список — сохранить для магазина.</p>
<div class="posts">{cards}</div>
</main>"""
    page("remont.html", "Ремонт под ключ: расчёт материалов для ванной, кухни и комнаты — Метраж",
         "Расчёт материалов на ремонт под ключ: ванная, кухня и комната по этапам — штукатурка, стяжка, плитка, обои, краска, ламинат. Бесплатно и без регистрации.",
         main, crumb="Ремонт под ключ", app=False, lastmod="2026-10-29", og_title="Ремонт под ключ",
         og_icon=ICONS["shtukaturka"])


# ---------- служебные страницы ----------

def mail_link():
    return f'<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>' if "@" in CONTACT_EMAIL else CONTACT_EMAIL


def text_page(fn, title, desc, h1, crumb, body, robots=None, in_sitemap=True, og_title=None):
    main = f"""<main class="wrap calc-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><span>{crumb}</span></nav>
<article class="article post">
<header class="post-head"><h1>{h1}</h1></header>
{body}
</article>
</main>"""
    page(fn, title, desc, main, crumb=crumb, app=False, robots=robots, in_sitemap=in_sitemap,
         lastmod="2026-10-29", og_title=og_title)


def build_privacy():
    body = f"""<p class="note">Это шаблон политики конфиденциальности. Владельцу сайта стоит сверить его с юристом и с требованиями закона о персональных данных (152-ФЗ).</p>
<p class="post-meta">Редакция от 29 октября 2026</p>
<h2>Кто отвечает за данные</h2>
<p>Оператор — владелец сайта metrazh.online. По любым вопросам о данных пишите на {mail_link()}.</p>
<h2>Какие данные собираются</h2>
<ul>
<li><b>Яндекс Метрика с Вебвизором.</b> Счётчик собирает обезличенную статистику посещений: какие страницы открыты, сколько времени на них проведено, откуда пришёл посетитель, тип устройства и браузера, примерный регион по IP-адресу. Вебвизор записывает действия на странице — прокрутку, клики, движения мыши, — чтобы было видно, где посетителям неудобно.</li>
<li><b>Cookie.</b> Яндекс Метрика сохраняет в браузере cookie, чтобы отличать новые визиты от повторных.</li>
<li><b>Ответ «Расчёт пригодился?».</b> Если вы нажмёте «Да» или «Нет» под результатом, ответ и необязательный текст из поля «Что было не так?» (до 200 символов) уходят в Яндекс Метрику вместе с названием калькулятора. Больше никуда они не отправляются. Не пишите в это поле имя, телефон и другие личные данные.</li>
<li><b>Данные в вашем браузере (localStorage).</b> Сайт запоминает размеры комнаты, чтобы не вводить их в каждом калькуляторе заново, ваш список покупок, то, что вы закрыли уведомление о cookie или уже ответили на вопрос «Расчёт пригодился?». Эти данные хранятся только в вашем браузере и никуда не отправляются.</li>
</ul>
<p>Имя, телефон, адрес и другие данные, по которым вас можно узнать, сайт не спрашивает и не собирает.</p>
<p>Шрифты сайта загружаются с самого metrazh.online, сторонние шрифтовые сервисы не используются.</p>
<h2>Зачем</h2>
<p>Статистика нужна, чтобы понимать, какими калькуляторами пользуются, где в них ошибаются, и улучшать сайт. Метрика также отмечает выполненные расчёты и переходы по ссылкам в магазин.</p>
<h2>Кому передаются данные</h2>
<p>Данные не продаются и не передаются третьим лицам для их собственных целей. Статистику обрабатывает сервис Яндекс Метрика по своим <a href="https://yandex.ru/legal/metrica_termsofuse/" rel="nofollow">условиям использования</a>. Если вы переходите в магазин по партнёрской ссылке, магазин и партнёрская сеть получают сведения о переходе по своим правилам.</p>
<h2>Как отключить cookie и статистику</h2>
<ul>
<li>Запретите cookie для сайта в настройках браузера или откройте сайт в режиме инкогнито.</li>
<li>Установите <a href="https://yandex.ru/support/metrica/general/opt-out.html" rel="nofollow">блокировщик Яндекс Метрики</a> — расширение для браузера от Яндекса.</li>
<li>Чтобы удалить размеры комнаты и список покупок, очистите данные сайта metrazh.online в настройках браузера.</li>
</ul>
<p>Калькуляторы продолжат работать и без cookie.</p>
<h2>Запросы и вопросы</h2>
<p>Чтобы задать вопрос о ваших данных или попросить их удалить, напишите на {mail_link()}.</p>"""
    text_page("privacy.html", "Политика конфиденциальности — Метраж",
              "Какие данные собирает сайт «Метраж»: Яндекс Метрика, cookie и данные в браузере. Зачем они нужны и как отключить cookie.",
              "Политика конфиденциальности", "Политика конфиденциальности", body, og_title="Политика конфиденциальности")


def build_about():
    body = f"""<p class="post-lead">«Метраж» — бесплатные строительные калькуляторы: сколько плитки, обоев, краски, смеси или кирпича нужно на комнату, чтобы купить материал один раз и без большого остатка.</p>
<h2>Зачем сделан сайт</h2>
<p>Перед ремонтом почти всегда приходится считать материалы вручную — и легко ошибиться: забыть вычесть дверь, не учесть запас на подрезку или округлить вниз. Калькуляторы делают этот расчёт за вас, показывают формулу и подсказывают, сколько упаковок или мешков брать.</p>
<h2>Как считаются результаты</h2>
<ul>
<li>Площадь — по размерам комнаты, окна и двери вычитаются.</li>
<li>Расход — по нормам из инструкций производителей и строительной практике. На каждой странице в разделе «Как считается» есть формула и таблица норм.</li>
<li>К результату добавляется запас на подрезку и бой, итог округляется вверх до целых штук, упаковок и мешков.</li>
</ul>
<h2>Расчёты ориентировочные</h2>
<p>Точный расход зависит от конкретной марки материала, ровности основания и способа укладки. Перед покупкой сверьтесь с рекомендациями на упаковке — там, где это возможно, введите расход производителя в калькулятор.</p>
<h2>Реклама и партнёрские ссылки</h2>
<p>В блоке «Купить» под калькуляторами стоят партнёрские ссылки на магазин. Если вы купите материал по такой ссылке, сайт получит небольшую комиссию — цена для вас не меняется. Такие блоки помечены как реклама: в маркировке указаны рекламодатель, его ИНН и идентификатор рекламы (erid).</p>
<h2>Данные</h2>
<p>Сайт ведёт обезличенную статистику через Яндекс Метрику, а размеры комнаты и список покупок хранит только в вашем браузере. Подробнее — в <a href="privacy.html">политике конфиденциальности</a>.</p>
<h2>Контакты</h2>
<p>Нашли ошибку в расчёте или хотите предложить калькулятор — пишите на {mail_link()}.</p>"""
    text_page("o-sajte.html", "О сайте «Метраж» — как работают строительные калькуляторы",
              "Зачем сделан сайт «Метраж», как считаются результаты калькуляторов, почему расчёты ориентировочные, партнёрские ссылки и контакты.",
              "О сайте «Метраж»", "О сайте", body, og_title="О сайте «Метраж»")


def build_list_page():
    body = """<p class="page-lead">Сюда попадают расчёты, которые вы добавили кнопкой «Добавить в список покупок». Список хранится только в этом браузере.</p>
<div id="list-root" class="list-root"><noscript><p>Для списка покупок нужен JavaScript.</p></noscript></div>"""
    text_page("spisok.html", "Список покупок — Метраж", "Ваш список материалов для ремонта из калькуляторов «Метража».",
              "Список покупок", "Список покупок", body, robots="noindex", in_sitemap=False)


def build_404():
    cards = "".join(card(h, name, d) for h, _, name, d in CALCS)
    main = f'''<main class="wrap home-hero">
<h1>Страница не найдена</h1>
<p class="lead">Возможно, ссылка устарела. Выберите нужный калькулятор:</p>
<div class="cards">{cards}</div>
</main>'''
    page("404.html", f"Страница не найдена — {SITE_NAME}", "Такой страницы нет. Выберите калькулятор.",
         main, robots="noindex", in_sitemap=False)


def build_seo_files():
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url, mod in sorted(SITEMAP, key=lambda x: x[0] != SITE_URL):
            prio = "1.0" if url == SITE_URL else "0.8"
            f.write(f"  <url><loc>{url}</loc><lastmod>{mod}</lastmod><priority>{prio}</priority></url>\n")
        f.write("</urlset>\n")
    # CNAME для GitHub Pages: свой домен берётся из SITE_URL.
    host = urlparse(SITE_URL).hostname
    cname = os.path.join(ROOT, "CNAME")
    if host.endswith(".github.io"):
        if os.path.exists(cname):
            os.remove(cname)
    else:
        with open(cname, "w", encoding="utf-8") as f:
            f.write(host + "\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /tools/\n\nSitemap: {SITE_URL}sitemap.xml\n")


if __name__ == "__main__":
    build_tile()
    build_wallpaper()
    build_paint()
    build_laminate()
    build_plaster()
    build_putty()
    build_drywall()
    build_insulation()
    build_screed()
    build_brick()
    build_hubs()
    build_index()   # после хабов: на главной их карточки
    build_article_tiles()
    build_stati()
    build_privacy()
    build_about()
    build_list_page()
    build_404()
    build_seo_files()
    with open(os.path.join(ROOT, "tools", "og", "pages.json"), "w", encoding="utf-8") as f:
        json.dump(OG_PAGES, f, ensure_ascii=False, indent=1)
    print(f"Собрано страниц: {len(SITEMAP) + 1}, sitemap: {len(SITEMAP)} адресов, SITE_URL = {SITE_URL}")
