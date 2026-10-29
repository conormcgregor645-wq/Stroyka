/*
 * Превью для соцсетей: assets/og/<страница>.png, 1200×630.
 * Список страниц — tools/og/pages.json (его пишет tools/build.py).
 *
 *   cd tools/og && npm install && node render.cjs
 *
 * Шрифты Manrope и JetBrains Mono берутся из npm-пакетов @fontsource.
 * Браузер — Chromium из Playwright (или путь в переменной CHROMIUM_PATH).
 */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "assets", "og");
const LIMIT = 150 * 1024;
const css = (pkg, w) => pathToFileURL(require.resolve(`@fontsource/${pkg}/${w}.css`)).href;

const RULER = '<svg width="208" height="20" viewBox="0 0 104 10"><rect width="104" height="10" rx="2" fill="#D9622B"/>' +
  '<g stroke="#1E2226" stroke-width="1.2">' + [6, 16, 26, 36, 46, 56, 66, 76, 86, 96]
    .map(x => `<line x1="${x}" y1="0" x2="${x}" y2="${x === 6 ? 6 : x === 56 ? 7 : 4}"/>`).join("") + "</g></svg>";

// Иконка материала на тёмном фоне: светлые линии, оранжевые заливки.
const lightIcon = svg => svg
  .replace(/stroke="#1E2226"/g, 'stroke="#F5F1EA"')
  .replace(/fill="#F7E2D5"/g, 'fill="rgba(240,162,122,.25)"')
  .replace(/width="34" height="34"/, 'width="210" height="210"');

function page(p) {
  const art = p.icon ? lightIcon(p.icon) : RULER.replace('width="208" height="20"', 'width="240" height="23"');
  const size = p.title.length > 34 ? 60 : p.title.length > 24 ? 68 : 78;
  return `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="${css("manrope", "800")}"><link rel="stylesheet" href="${css("manrope", "600")}">
<link rel="stylesheet" href="${css("jetbrains-mono", "700")}">
<style>
  * { box-sizing: border-box; margin: 0; }
  body { width: 1200px; height: 630px; overflow: hidden; background-color: #1E2226; color: #F5F1EA; font-family: Manrope, sans-serif;
    background-image: linear-gradient(rgba(245,241,234,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(245,241,234,.07) 1px, transparent 1px),
      linear-gradient(rgba(245,241,234,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(245,241,234,.03) 1px, transparent 1px);
    background-size: 50px 50px, 50px 50px, 10px 10px, 10px 10px; position: relative; }
  .logo { position: absolute; left: 80px; top: 64px; display: flex; flex-direction: column; gap: 8px; }
  .logo b { font-size: 44px; font-weight: 800; letter-spacing: -1px; line-height: 1; }
  h1 { position: absolute; left: 80px; top: 230px; width: 700px; font-size: ${size}px; line-height: 1.08; font-weight: 800; letter-spacing: -1.5px; }
  .bar { position: absolute; left: 80px; bottom: 132px; width: 140px; height: 10px; background: #D9622B; border-radius: 2px; }
  .foot { position: absolute; left: 80px; bottom: 64px; font-size: 26px; font-weight: 600; color: #C9C4BB; }
  .foot span { font-family: "JetBrains Mono", monospace; font-weight: 700; color: #F0A27A; }
  .art { position: absolute; right: 80px; top: 165px; width: 300px; height: 300px; border: 3px solid #D9622B; border-radius: 28px;
    display: flex; align-items: center; justify-content: center; background: rgba(245,241,234,.04); box-shadow: 14px 14px 0 #D9622B; }
</style></head><body>
<div class="logo"><b>Метраж</b>${RULER}</div>
<h1>${p.title}</h1>
<div class="bar"></div>
<div class="foot"><span>metrazh.online</span> · бесплатные строительные калькуляторы</div>
<div class="art">${art}</div>
</body></html>`;
}

(async () => {
  const pages = JSON.parse(fs.readFileSync(path.join(ROOT, "tools", "og", "pages.json"), "utf8"));
  const only = process.argv.slice(2);
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const tab = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  for (const p of pages.filter(p => !only.length || only.includes(p.slug))) {
    const tmp = path.join(OUT, `.${p.slug}.html`);
    fs.writeFileSync(tmp, page(p));
    await tab.goto(pathToFileURL(tmp).href);
    await tab.evaluate(() => document.fonts.ready);
    const file = path.join(OUT, `${p.slug}.png`);
    await tab.screenshot({ path: file, type: "png" });
    fs.unlinkSync(tmp);
    const kb = fs.statSync(file).size;
    console.log(`${p.slug}.png  ${(kb / 1024).toFixed(1)} КБ${kb > LIMIT ? "  ← больше 150 КБ!" : ""}`);
  }
  await browser.close();
})();
