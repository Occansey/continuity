/**
 * Capture the deployed Continuity product as a still sequence for the film.
 * Reuses the browser + puppeteer-core installed for the Geminga film — no new install.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const require = createRequire("/Users/maxwell/hackathon/film/");
const puppeteer = require("puppeteer-core");

const URL = "https://continuity-468826425509.us-central1.run.app";
const OUT = path.join(import.meta.dirname, "public", "take");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "shell", args: ["--hide-scrollbars"] });
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
const client = await page.createCDPSession();
await client.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 2, mobile: false });
await page.goto(URL, { waitUntil: "networkidle0", timeout: 90_000 });
await sleep(1500);

const frames = [];
let n = 0;
async function grab() { await page.screenshot({ path: path.join(OUT, `f${String(n).padStart(3,"0")}.jpg`), type: "jpeg", quality: 82 }); frames.push(n); n++; }

// hero, then a slow scroll through the findings
await grab();
for (let y = 0; y < 3200; y += 240) {
  await page.evaluate((yy) => window.scrollTo(0, yy), y);
  await sleep(260); await grab();
}
// click the "across scenes" filter to show the cross-scene findings
await page.evaluate(() => { const b=[...document.querySelectorAll(".filters button")].find(x=>/across/.test(x.textContent)); b&&b.click(); });
await page.evaluate(() => window.scrollTo(0, 600)); await sleep(500); await grab(); await grab();

await browser.close();
const first = fs.readFileSync(path.join(OUT, "f000.jpg"));
console.log(`  ${frames.length} frames captured`);
