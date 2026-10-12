/*
 * Партнёрские ссылки строительных магазинов.
 *
 * Чтобы зарабатывать, замените шаблоны на свои партнёрские ссылки
 * (Admitad, Яндекс Дистрибуция, Where-to-buy и т.п.).
 *
 *   search  — ссылка на поиск в магазине, {q} заменяется на поисковый запрос.
 *   wrap    — обёртка партнёрской сети (deeplink), {url} заменяется на
 *             закодированную ссылку на магазин. Оставьте "{url}", если
 *             партнёрки пока нет — ссылка будет вести прямо в магазин.
 *
 * Пример для Admitad:  wrap: "https://ad.admitad.com/g/ВАШ_КОД/?ulp={url}"
 *
 * Перед запуском проверьте, что поисковые URL магазинов актуальны.
 */
window.PARTNERS = [
  {
    name: "Лемана ПРО",
    search: "https://lemanapro.ru/search/?q={q}",
    wrap: "{url}"
  },
  {
    name: "Петрович",
    search: "https://petrovich.ru/search/?q={q}",
    wrap: "{url}"
  },
  {
    name: "ВсеИнструменты",
    search: "https://www.vseinstrumenti.ru/search/?what={q}",
    wrap: "{url}"
  },
  {
    name: "Яндекс Маркет",
    search: "https://market.yandex.ru/search?text={q}",
    wrap: "{url}"
  }
];
