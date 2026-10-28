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
import json
import math
import os
import re
from urllib.parse import parse_qs, urlencode, urlparse

# ===== НАСТРОЙКИ =====
# Базовый адрес сайта со слешем на конце. После переезда на свой домен
# поменяйте здесь и пересоберите: обновятся canonical, og:url, sitemap и robots.
SITE_URL = "https://metrazh.online/"
# Название сайта: шапка, подвал, og:site_name, заголовок страницы 404.
SITE_NAME = "Метраж"
# Дата для <lastmod> в sitemap.xml.
LASTMOD = "2026-10-12"
# Подтверждение сайта в партнёрской сети Mitgo (Admitad) — только на главной.
MITGO_VERIFY = '\n<meta name="mitgo-verification" content="5d60c4fe-cbf5-4f7c-a4eb-ab32dc9be0b9" />'
# Номер счётчика Метрики для <noscript> — тот же, что в assets/site.js.
metrika_counter = "113822395"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Иконки сайта: assets/favicon.svg (логотип-рулетка) и assets/apple-touch-icon.png (180×180).
ICONS_HEAD = ('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n'
              '<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">')

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
    "nalivnoy-pol": _SVG.format(extra=' stroke-linejoin="round"', body='<rect x="2" y="16" width="20" height="5"/><path d="M2 16v-3h20v3" fill="#D9622B"/><path d="M12 2c2 2.8 3 4.3 3 5.6a3 3 0 0 1-6 0C9 6.3 10 4.8 12 2z"/>'),
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
    ("nalivnoy-pol.html", "Наливной пол", "Наливной пол", "Мешки по толщине слоя"),
    ("kirpich.html", "Кирпич", "Кирпич", "Штуки и раствор"),
]
# Статьи: файл, заголовок (H1), описание для списка, дата публикации (ISO), дата для людей.
ARTICLES = [
    ("skolko-plitki-na-vannuyu.html",
     "Сколько плитки нужно на ванную: готовые расчёты для 2×2, 2×3 и 3×3 м",
     "Таблица с плиткой, упаковками, клеем и затиркой для трёх типовых ванных, как измерить комнату, что вычесть и сколько брать запаса.",
     "2026-11-01T09:00:00+03:00", "1 ноября 2026"),
]
ARTICLE_FILES = {a[0] for a in ARTICLES} | {"stati.html"}

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


ROOM3 = h3("Помещение") + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3"), field("room_h", "Высота, м", "2.7"))
ROOM2 = h3("Помещение") + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3"), cols=2)


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
    return links + articles + f'<a class="nav-all" href="{all_href}">Все калькуляторы</a>'


def page(fn, title, desc, main_html, faq=None, crumb=None, robots=None, in_sitemap=True, after_main="", verify="",
         trail=(), ld_extra=(), app=True, lastmod=None):
    """trail — промежуточные крошки [(название, файл)]; ld_extra — дополнительная разметка Schema.org;
    app — добавлять WebApplication (для калькуляторов); lastmod — дата для sitemap."""
    canon = SITE_URL + ("" if fn == "index.html" else fn)

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
    scripts = '\n<script src="assets/partners.js"></script>\n<script src="assets/calc.js"></script>' if is_calc else ""
    robots_meta = f'\n<meta name="robots" content="{robots}">' if robots else ""
    footer_links = '<a href="index.html">Все калькуляторы</a><a href="stati.html">Статьи</a>' + "".join(f'<a href="{h}">{t}</a>' for h, t, *_ in CALCS)
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
<meta name="theme-color" content="#1E2226">
<!-- Подтверждение прав в Яндекс Вебмастере: раскомментируйте и вставьте код -->
<!-- <meta name="yandex-verification" content="YANDEX_VERIFICATION_CODE"> -->
<!-- Подтверждение прав в Google Search Console: раскомментируйте и вставьте код -->
<!-- <meta name="google-site-verification" content="GOOGLE_VERIFICATION_CODE"> -->{verify}
{ICONS_HEAD}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&amp;family=Manrope:wght@400;500;600;700;800&amp;display=swap">
<link rel="stylesheet" href="assets/style.css">{ldhtml}
</head>
<body>
<header class="site-header"><div class="wrap header-bar">
<a class="logo" href="index.html"><span class="logo-name">{SITE_NAME}</span>{RULER}</a>
<nav class="nav" aria-label="Основное меню">{nav_html(fn)}</nav>
</div></header>
{main_html}{after_main}
<footer class="site-footer"><div class="wrap">
<p class="footer-text"><strong>{SITE_NAME}</strong> · {host} — бесплатные строительные калькуляторы. Расчёты приблизительные, сверяйтесь с рекомендациями производителя.</p>
<span class="footer-copy">© 2026</span>
<nav class="footer-links" aria-label="Все калькуляторы">{footer_links}</nav>
</div></footer>
<!-- Яндекс Метрика: код счётчика в assets/site.js, здесь — запасной вариант без JavaScript -->
<noscript><div><img src="https://mc.yandex.ru/watch/{metrika_counter}" style="position:absolute; left:-9999px;" alt=""></div></noscript>{scripts}
<script src="assets/site.js"></script>
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


def calc_page(fn, title, desc, h1, calc_type, buy_title, plan_title, inputs, how, norms, faq, related="", lastmod=None):
    """Страница калькулятора: форма и результат, схема, покупка, реклама, «Как считается», нормы, FAQ."""
    main = f'''<main class="wrap calc-page">
<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="index.html">Главная</a><span aria-hidden="true">→</span><span>{h1}</span></nav>
<div class="calc-head"><h1>{h1}</h1><span class="calc-tagline">Формулы как у мастеров · Без регистрации</span></div>
{calc_form(calc_type, inputs, plan_title)}
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
    page(fn, title, desc, main, faq, crumb=h1, after_main=MBAR, lastmod=lastmod)


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
<defs><pattern id="hTiles" x="40" y="30" width="26" height="26" patternUnits="userSpaceOnUse"><rect width="26" height="26" fill="#F7E2D5"/><path d="M26 0V26H0" fill="none" stroke="#D9622B" stroke-width="1"/></pattern></defs>
<rect x="40" y="30" width="260" height="156" fill="url(#hTiles)" stroke="#1E2226" stroke-width="2"/>
<g stroke="#1E2226" stroke-width="1"><line x1="40" y1="14" x2="300" y2="14"/><line x1="40" y1="9" x2="40" y2="19"/><line x1="300" y1="9" x2="300" y2="19"/><line x1="316" y1="30" x2="316" y2="186"/><line x1="311" y1="30" x2="321" y2="30"/><line x1="311" y1="186" x2="321" y2="186"/></g>
<rect x="148" y="5" width="44" height="18" fill="#FFFDF9"/><text x="170" y="18" text-anchor="middle" class="svg-num">3,0 м</text>
<rect x="303" y="99" width="30" height="18" fill="#FFFDF9"/><text x="318" y="112" text-anchor="middle" class="svg-num">2,0</text>
</svg>'''
    main = f'''<main>
<section class="wrap home-hero" id="calc">
<h1>Сколько материала нужно на&nbsp;ремонт?</h1>
<div class="pills">{pills}</div>
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
         main, faq, verify=MITGO_VERIFY)


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
    inputs = (h3("Что утепляем") + seg("surface", [("walls", "Стены"), ("floor", "Пол или перекрытие")], "walls")
              + ROOM3 + openings("surface:walls")
              + h3("Утеплитель") + grid(select("total_mm", "Толщина утепления", [("50", "50 мм"), ("100", "100 мм"), ("150", "150 мм"), ("200", "200 мм")], "100"),
                                        field("board_t", "Толщина плиты, мм", "50"), field("per_pack", "Плит в упаковке", "8", "number", ' min="0" step="1"'))
              + grid(field("board_l", "Длина плиты, мм", "1200"), field("board_w", "Ширина плиты, мм", "600"),
                     price("Цена упаковки, ₽"), top=True)
              + reserve([("3", "минимум"), ("5", "рекомендуем"), ("10", "сложная форма")], "5"))
    how = '''<p>Число слоёв = требуемая толщина ÷ толщина плиты (вверх). Плиты = площадь × слои + запас, делённые на площадь одной плиты, с округлением вверх. Затем плиты пересчитываются в упаковки.</p>
<p>Пароизоляцию кладут с нахлёстом 10 см — плюс 10% к площади. Для стен добавляем тарельчатые дюбели — около 6 штук на м².</p>'''
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
               ("Когда можно ходить по стяжке?", "Обычно через 2–3 дня, а класть ламинат или плитку — после полного высыхания: около недели на каждый сантиметр толщины для цементной стяжки.")],
              related='<h2>По теме</h2>\n<div class="posts">' + calc_card("nalivnoy-pol.html", "Калькулятор наливного пола",
                  "Смесь в килограммах и мешках по толщине слоя для тонкого выравнивания пола.") + "</div>")


def build_selflevel():
    inputs = (h3("Площадь") + seg("area_mode", [("dims", "По размерам комнаты"), ("area", "Ввести площадь")], "dims")
              + grid(field("room_l", "Длина, м", "4", show="area_mode:dims"), field("room_w", "Ширина, м", "3", show="area_mode:dims"),
                     field("area", "Площадь, м²", "12", show="area_mode:area"), top=True)
              + h3("Толщина слоя") + grid(field("min_mm", "В самом тонком месте, мм", "10"), field("max_mm", "В самом толстом месте, мм", "10"))
              + '<p class="hint">Перепад измеряют уровнем или лазерным нивелиром. Расчёт идёт по средней толщине: (тонкое место + толстое) / 2.</p>'
              + h3("Смесь") + seg("mixtype", [("finish", "Финишная (тонкий слой)"), ("base", "Базовая (толстый слой)"), ("custom", "Свой расход")], "finish")
              + grid(field("rate", "Расход, кг/м² на 1 мм", "1.6", show="mixtype:custom"), top=True)
              + '<p class="hint">По умолчанию — 1,6 кг на 1 м² при слое 1 мм. Точный расход указан на мешке.</p>'
              + h3("Мешок") + seg("bag", [("20", "20 кг"), ("25", "25 кг")], "25")
              + reserve([("0", "без запаса"), ("5", "рекомендуем"), ("10", "неровное основание")], "5", "Запас")
              + grid(price("Цена мешка, ₽"), top=True))

    def mix(area, t, rate=1.6, res=5, bag=25):
        kg = math.ceil(area * t * rate * (1 + res / 100) * 100 - 1e-7) / 100
        return kg, up(kg / bag)
    kg12, bags12 = mix(12, 10)
    kg10, bags10 = mix(10, 10)
    bags10_20 = mix(10, 10, bag=20)[1]
    how = f'''<p>Масса смеси = площадь × средняя толщина слоя (мм) × расход на 1 мм + запас. Средняя толщина — это (толщина в самом тонком месте + толщина в самом толстом) / 2. Количество мешков округляется вверх до целого.</p>
<p><b>Пример: комната 4×3 м, слой 10 мм.</b> Площадь — 4 × 3 = 12 м². Смесь без запаса: 12 м² × 10 мм × 1,6 кг = 192 кг. С запасом 5%: 192 × 1,05 = {ru_num(kg12, 2)} кг. Мешков по 25 кг: {ru_num(kg12, 2)} / 25 = 8,06 — значит, нужно {bags12}: восьми не хватит. Грунтовка — около 0,15 л на м², на 12 м² это 1,8 л. Демпферную ленту клеят по периметру: 2 × (4 + 3) = 14 м.</p>
<p>Если пол неровный, измерьте толщину в самом высоком и самом низком месте. Например, при слое 5 мм в одном углу и 15 мм в другом средняя толщина — 10 мм.</p>'''
    norms = (table(["Смесь", "Толщина слоя", "Расход на 1 мм", "Высыхание"],
                   [["Финишная", "2–10 мм", "смотрите на упаковке", "смотрите на упаковке"],
                    ["Базовая", "10–100 мм", "смотрите на упаковке", "смотрите на упаковке"],
                    ["Гипсовая", "смотрите на упаковке", "смотрите на упаковке", "смотрите на упаковке"]])
             + "\n<p>Расход и сроки высыхания у разных марок отличаются, поэтому калькулятор по умолчанию берёт ориентир 1,6 кг на 1 м² при слое 1 мм, а точное значение можно ввести в режиме «Свой расход». Гипсовые смеси используют в сухих помещениях. Грунтовка — около 0,15 л на м².</p>")
    calc_page("nalivnoy-pol.html",
              "Калькулятор наливного пола — сколько смеси в кг и мешках по толщине слоя",
              "Калькулятор наливного пола онлайн: сколько килограммов и мешков смеси нужно по площади и толщине слоя с учётом перепада, плюс грунтовка и демпферная лента.",
              "Калькулятор наливного пола",
              "selflevel", "Купить наливной пол и грунтовку", "Разрез пола", inputs, how, norms,
              [("Сколько мешков наливного пола нужно на 10 м² при слое 1 см?",
                f"При расходе 1,6 кг на 1 м² на каждый миллиметр: 10 м² × 10 мм × 1,6 = 160 кг, с запасом 5% — {ru_num(kg10, 2)} кг. Это {bags10} мешков по 25 кг или {bags10_20} мешков по 20 кг. Точный расход своей смеси смотрите на мешке."),
               ("Чем наливной пол отличается от стяжки?",
                "Наливной пол — самовыравнивающаяся смесь: её разводят до жидкого состояния, она растекается и сама образует ровную поверхность. Его заливают тонким слоем для выравнивания. Цементно-песчаную стяжку делают толще и разравнивают правилом по маякам. При большом перепаде стяжка обходится дешевле."),
               ("Нужна ли грунтовка под наливной пол?",
                "Да. Грунтовка уменьшает впитывание основания, чтобы вода из смеси не уходила в бетон раньше времени, и улучшает сцепление. Без неё на поверхности могут появиться пузыри и трещины. Ориентир расхода — около 0,15 л на м², точный указан на ёмкости."),
               ("Как измерить перепад пола?",
                "Лазерным нивелиром или длинным уровнем с правилом найдите самую высокую и самую низкую точку пола. Над самой высокой точкой будет самый тонкий слой — не меньше, чем допускает инструкция смеси. В самом низком месте слой толще на величину перепада. Эти два значения и вводите в калькулятор.")],
              related='<h2>По теме</h2>\n<div class="posts">' + calc_card("styazhka.html", "Калькулятор стяжки пола",
                  "Мешки сухой смеси или цемент с песком — если перепад большой и нужен толстый слой.") + "</div>",
              lastmod="2026-11-08")


def build_brick():
    bricks = [("65", "Одинарный 250×120×65"), ("88", "Полуторный 250×120×88"), ("138", "Двойной 250×120×138")]
    walls = [("0.5", "В полкирпича (120 мм)"), ("1", "В кирпич (250 мм)"), ("1.5", "В 1,5 кирпича (380 мм)"), ("2", "В 2 кирпича (510 мм)")]
    inputs = (h3("Что кладём") + seg("mode", [("perimeter", "Стены по периметру"), ("one", "Одна стена")], "perimeter")
              + h3("Размеры") + grid(field("room_l", "Длина, м", "4"), field("room_w", "Ширина, м", "3", show="mode:perimeter"),
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

def calc_card(fn, title, desc):
    return (f'<a class="post-card" href="{fn}"><span class="eyebrow">Калькулятор</span>'
            f'<span class="post-title">{title}</span><span class="post-desc">{desc}</span>'
            f'<span class="post-go">Рассчитать →</span></a>')


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
         main, crumb="Статьи", app=False, lastmod=ARTICLES[0][3][:10])


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
         ld_extra=[article_ld], app=False, lastmod=iso[:10])
    return results


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
        for url, mod in SITEMAP:
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
    build_index()
    build_tile()
    build_wallpaper()
    build_paint()
    build_laminate()
    build_plaster()
    build_putty()
    build_drywall()
    build_insulation()
    build_screed()
    build_selflevel()
    build_brick()
    build_article_tiles()
    build_stati()
    build_404()
    build_seo_files()
    print(f"Собрано страниц: {len(SITEMAP) + 1}, sitemap: {len(SITEMAP)} адресов, SITE_URL = {SITE_URL}")
