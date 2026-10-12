/*
 * Монетизация: партнёрские ссылки на материалы и магазины.
 *
 * 1. AFFILIATE — главная кнопка «Купить →» в блоке «Купить материал».
 *    Замените заглушку AFFILIATE_URL_… на свою партнёрскую ссылку на товар
 *    или категорию (Admitad, Яндекс Маркет для партнёров и т.п.).
 *    Пока заглушка не заменена, кнопка ведёт на поиск товара в первом
 *    магазине из списка PARTNERS — битых ссылок на сайте не будет.
 *
 * 2. PARTNERS — ссылки «Сравнить цены» под кнопкой.
 *    search — поиск в магазине, {q} заменяется на запрос.
 *    wrap   — обёртка партнёрской сети (deeplink), {url} заменяется на
 *             закодированную ссылку на магазин; "{url}" — без партнёрки.
 *    Пример для Admitad:  wrap: "https://ad.admitad.com/g/ВАШ_КОД/?ulp={url}"
 *
 * Все ссылки выводятся с rel="sponsored nofollow" и target="_blank".
 */
window.AFFILIATE = {
  // Плитка
  PLITKA: "AFFILIATE_URL_PLITKA",
  KLEY_PLITOCHNY: "AFFILIATE_URL_KLEY_PLITOCHNY",
  ZATIRKA: "AFFILIATE_URL_ZATIRKA",
  // Обои
  OBOI: "AFFILIATE_URL_OBOI",
  KLEY_OBOYNY: "AFFILIATE_URL_KLEY_OBOYNY",
  // Краска и общее
  KRASKA: "AFFILIATE_URL_KRASKA",
  GRUNTOVKA: "AFFILIATE_URL_GRUNTOVKA",
  MALYARNY_INSTRUMENT: "AFFILIATE_URL_MALYARNY_INSTRUMENT",
  // Ламинат
  LAMINAT: "AFFILIATE_URL_LAMINAT",
  PODLOZHKA: "AFFILIATE_URL_PODLOZHKA",
  PLINTUS: "AFFILIATE_URL_PLINTUS",
  // Штукатурка и шпаклёвка
  SHTUKATURKA: "AFFILIATE_URL_SHTUKATURKA",
  MAYAKI: "AFFILIATE_URL_MAYAKI",
  SHPAKLEVKA_START: "AFFILIATE_URL_SHPAKLEVKA_START",
  SHPAKLEVKA_FINISH: "AFFILIATE_URL_SHPAKLEVKA_FINISH",
  // Гипсокартон
  GIPSOKARTON: "AFFILIATE_URL_GIPSOKARTON",
  PROFIL_GKL: "AFFILIATE_URL_PROFIL_GKL",
  SAMOREZY: "AFFILIATE_URL_SAMOREZY",
  // Утеплитель
  UTEPLITEL: "AFFILIATE_URL_UTEPLITEL",
  PAROIZOLYACIYA: "AFFILIATE_URL_PAROIZOLYACIYA",
  DYUBELI_GRIBKI: "AFFILIATE_URL_DYUBELI_GRIBKI",
  // Стяжка
  PESKOBETON: "AFFILIATE_URL_PESKOBETON",
  NALIVNOY_POL: "AFFILIATE_URL_NALIVNOY_POL",
  CEMENT: "AFFILIATE_URL_CEMENT",
  PESOK: "AFFILIATE_URL_PESOK",
  FIBRA: "AFFILIATE_URL_FIBRA",
  DEMPFERNAYA_LENTA: "AFFILIATE_URL_DEMPFERNAYA_LENTA",
  // Кирпич
  KIRPICH: "AFFILIATE_URL_KIRPICH",
  KLADOCHNAYA_SETKA: "AFFILIATE_URL_KLADOCHNAYA_SETKA"
};

// Перед запуском проверьте, что поисковые URL магазинов актуальны.
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
