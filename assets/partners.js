/*
 * Партнёрские ссылки: блок «Купить …» под каждым калькулятором.
 *
 * links — партнёрские ссылки Максидома (через uuwgc.com). Все ссылки на
 *         покупку должны вести через партнёрскую сеть, не напрямую на maxidom.ru.
 * pages — что показывать на каждом калькуляторе: main — большая кнопка,
 *         extra — маленькие кнопки под ней [ключ ссылки, подпись].
 * advertiser, inn — для маркировки «Реклама». erid берётся из параметра
 *         erid каждой ссылки автоматически.
 */
window.SHOP = {
  id: "maxidom",
  button: "Купить в Максидоме",
  advertiser: "ООО МАКСИДОМ",
  inn: "7804064663",
  links: {
    PLITKA: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fplitka%2F",
    KLEY_PLITOCHNY: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fklei-dlya-plitki-keramicheskoy-i-keramogranita%2F",
    ZATIRKA: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fzatirki-dlya-plitki-keramicheskoy-i-keramogranita%2F",
    OBOI: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Foboi%2F",
    KRASKA: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fkraski-dlya-sten-i-potolkov%2F",
    GRUNTOVKA: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fgruntovka%2F",
    LAMINAT: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Flaminat%2F",
    GIPSOKARTON: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fgipsokarton%2F",
    // Штукатурка, шпаклёвка, утеплитель, стяжка, кирпич — раздел «Строительные материалы».
    OSTALNOE: "https://uuwgc.com/g/vw6dqabpgkfe6c34cc86b6a2cdd7f0/?erid=25H8d7vbP8SRTvH4HtSZJ1&ulp=https%3A%2F%2Fwww.maxidom.ru%2Fcatalog%2Fstroitelnye-materialy%2F"
  },
  pages: {
    tile: { main: "PLITKA", extra: [["KLEY_PLITOCHNY", "Клей для плитки"], ["ZATIRKA", "Затирка"]] },
    wallpaper: { main: "OBOI" },
    paint: { main: "KRASKA", extra: [["GRUNTOVKA", "Грунтовка"]] },
    laminate: { main: "LAMINAT" },
    drywall: { main: "GIPSOKARTON" },
    plaster: { main: "OSTALNOE" },
    putty: { main: "OSTALNOE" },
    insulation: { main: "OSTALNOE" },
    screed: { main: "OSTALNOE" },
    brick: { main: "OSTALNOE" }
  }
};
