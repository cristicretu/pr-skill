#!/usr/bin/env node
// Capture a web interaction frame by frame on a stepped clock, so the result
// is exact and repeatable instead of a janky screen recording. Works for any
// framework (Next.js, Vite, Remix, plain HTML): it drives a real browser.
//
//   node web-frames.mjs --url http://localhost:3000/cart --out frames/ \
//     --clip "#checkout" --action "click:button[data-open]" \
//     --frames 40 --step 8 [--scheme dark] [--width 390 --height 844] [--scale 2]
//
// Two clocks are stepped together each frame:
//   - Playwright's fake clock (Date, timers, requestAnimationFrame,
//     performance.now), which drives JS animation: Motion/framer-motion
//     springs, react-spring, GSAP, hand-written rAF loops.
//   - Every Web Animation in the document (CSS transitions, CSS keyframe
//     animations, element.animate(), and what Motion hands to WAAPI) is paused
//     and scrubbed to its own elapsed time, since the compositor does not
//     follow the fake clock.
//
// --action is run once after frame 0, then frames are stepped. Forms:
//   click:<selector>  hover:<selector>  press:<key>  fill:<selector>=<text>
//   eval:<js expression run in the page>
//   file:<path to an .mjs exporting default async (page) => {}>
// --setup takes the same forms and runs before frame 0 (open a menu, scroll).
// --probe <js expression> is evaluated after every frame and logged, and
//   saved as probe.txt: check an easing numerically, or pass the values to
//   strip.py --labels. e.g. --probe "getComputedStyle(box).opacity"
// --still skips the animation stepping and writes one screenshot (--out is a .png).
//
// Playwright is resolved from the current project (run this from the repo
// root that has it installed), or set PLAYWRIGHT_PATH to its package dir.
import { createRequire } from "node:module";
import { mkdirSync, readdirSync, unlinkSync, writeFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, v, i, all) => {
    if (v.startsWith("--")) acc.push([v.slice(2), all[i + 1]?.startsWith("--") || all[i + 1] === undefined ? "1" : all[i + 1]]);
    return acc;
  }, []),
);
if (!args.url || !args.out) {
  console.error("usage: web-frames.mjs --url URL --out DIR [--action ...] [--frames N] [--step MS]");
  process.exit(2);
}
const require = createRequire(pathToFileURL(resolve(process.cwd(), "noop.js")));
let playwright;
for (const name of [process.env.PLAYWRIGHT_PATH, "playwright", "@playwright/test", "playwright-core"].filter(Boolean)) {
  try { playwright = require(name); break; } catch {}
}
if (!playwright) {
  console.error("Playwright not found. pnpm add -D playwright && pnpm exec playwright install chromium");
  process.exit(1);
}

const frames = Number(args.frames ?? 40);
const step = Number(args.step ?? 1000 / 60);
const browser = await playwright.chromium.launch();
const context = await browser.newContext({
  viewport: { width: Number(args.width ?? 1280), height: Number(args.height ?? 800) },
  deviceScaleFactor: Number(args.scale ?? 2),
  colorScheme: args.scheme ?? "light",
  reducedMotion: args["reduced-motion"] ? "reduce" : "no-preference",
});
const page = await context.newPage();
const start = Date.parse("2026-01-15T09:41:00");
await page.clock.install({ time: start });
await page.goto(args.url, { waitUntil: "load" });
// Pages with open streams or sockets never go network-idle; don't wait forever.
await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
await page.evaluate(() => document.fonts.ready);
// install() lets fake time flow at wall-clock speed, so pause relative to the
// page's current time (a slow load may be past any fixed target), 2 s ahead to
// skip entrance animations. From here only runFor() moves time.
await page.clock.pauseAt((await page.evaluate(() => Date.now())) + 2000);
await settle(page);

async function run(spec) {
  if (!spec) return;
  const [kind, ...rest] = spec.split(":");
  const value = rest.join(":");
  if (kind === "click") await page.click(value);
  else if (kind === "hover") await page.hover(value);
  else if (kind === "press") await page.keyboard.press(value);
  else if (kind === "fill") { const at = value.indexOf("="); await page.fill(value.slice(0, at), value.slice(at + 1)); }
  else if (kind === "eval") await page.evaluate(value);
  else if (kind === "file") await (await import(pathToFileURL(resolve(value)))).default(page);
  else throw new Error(`unknown action ${spec}`);
}

async function settle(page) {
  await page.evaluate(() => {
    for (const a of document.getAnimations()) {
      if (a.effect?.getTiming().iterations === Infinity) continue;
      try { a.finish(); } catch {}
    }
  });
}

async function shoot(path) {
  const opts = { path, caret: "hide", animations: "allow" };
  if (args.clip) await page.locator(args.clip).first().screenshot(opts);
  else await page.screenshot(opts);
}

await run(args.setup);
if (args.still) {
  await settle(page);
  await shoot(args.out);
  console.log(args.out);
  await browser.close();
  process.exit(0);
}

mkdirSync(args.out, { recursive: true });
for (const f of readdirSync(args.out)) if (/^frame_\d{4}\.png$/.test(f)) unlinkSync(join(args.out, f));

const probes = [];
async function probe(i) {
  if (!args.probe) return;
  const v = await page.evaluate(args.probe);
  probes.push(String(v));
  console.log(`frame ${i}: ${v}`);
}
await shoot(join(args.out, "frame_0000.png"));
await probe(0);
await run(args.action);
let elapsed = 0;
for (let i = 1; i < frames; i++) {
  elapsed += step;
  await page.clock.runFor(step);
  await page.evaluate(([elapsed, step]) => {
    // An animation first seen now was started during the step just run.
    const born = (window.__vprBorn ??= new WeakMap());
    for (const a of document.getAnimations()) {
      if (!born.has(a)) born.set(a, elapsed - step);
      a.pause();
      a.currentTime = elapsed - born.get(a);
    }
  }, [elapsed, step]);
  await shoot(join(args.out, `frame_${String(i).padStart(4, "0")}.png`));
  await probe(i);
}
if (args.probe) writeFileSync(join(args.out, "probe.txt"), probes.join("\n") + "\n");
console.log(`${args.out}: ${frames} frames, ${step.toFixed(2)} ms apart`);
await browser.close();
