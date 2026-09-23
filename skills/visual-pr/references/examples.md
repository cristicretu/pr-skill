# The reference PRs, annotated

Five PRs on cristicretu/diri (a Rust/GPUI desktop app) set the bar this skill encodes. Agents working overnight wrote them from an orchestrator's brief. The agents couldn't record the screen, so every image was rendered headlessly from a synthetic fixture on an injected clock.

## What each one did

**#459: cursor blink and glide** (`cursor-motion/`)
- Opens with the felt problem: "The terminal cursor is a static block that teleports". Then a GIF of typing followed by idle, before any list.
- Main vs branch GIF, "same input script (typing, then a held left arrow at the 33 ms key-repeat rate)".
- A slow-motion GIF plus a **frame strip with two label rows per tile**: the opacity (`95% … 28% … 100%`) and the time (`33 ms … 700 ms`), titled "one blink cycle: the 12 frames it paints (six 33 ms steps per fade); the holds between them paint nothing". The strip proves a performance claim and a design claim at once.
- Discloses how the "main" panel was made: the branch with `reduce_motion(true)`, which takes the unchanged static path, "the paint fixture below is byte-identical to main".
- How section: "Curve choices, from looking at frames", including what changed after looking (16 paints per cycle cut to 12, because two were invisible frames).

**#460: pixel-smooth scrollback** (`pixel-smooth-scrollback/`)
- A scripted fling, "decelerating, 11 px per event tapering off, one event per 120 Hz frame", replayed on main and branch.
- A zoomed slow GIF at device-pixel scale: "Main holds still and then jumps a row; the branch moves one device pixel per event".
- A still resting mid-row to prove the overlays (selection, diff backgrounds, link underline, progress bar) stay attached to their text. It's an edge-case sheet disguised as a normal screen.
- Verification with a measurable visual claim: "every frame's interior is an exact 1-device-pixel translation of the previous one (max channel difference 0)".

**#464: perceptual faint text** (`perceptual-faint/`)
- **Measured the premise before building and reported that it was weaker than assumed**: "both turned out smaller than assumed. The numbers are below so the merge decision can be made on them." The later brief called this "the most valuable thing they did".
- Swatch grids of every palette color across three themes, plus realistic transcripts.
- The honest pair: glass at real coverage ("The text difference is not visible at this coverage"), then an exaggerated fixture labelled "**This is not what the terminal ships**; it is here only to show the mechanism".
- A table of evenness across 17 themes before and after. A table is also a visual.

**#465: Oklab theme crossfade** (`theme-crossfade/`)
- Four GIFs, each answering its own question: palette preview while arrowing (hard cut on the left, fade on the right), key held through the whole catalog, dark to light, dark to dark.
- A midpoint comparison (sRGB vs Oklab at t = 0.5) and a steps strip, followed by "An honest reading of that last pair: for whole themes the difference is modest, not dramatic".
- **Review first** lists the four places the author was least sure about, including "I could only judge motion from frames, not from a moving screen".
- A committed, documented fixture (`render_theme_fade_frames`) whose header gives the exact command that produced the GIFs.

**#476: hollow cursor in unfocused panes** (`hollow-cursor/`)
- Before/after of two panes in dark and light, captioned in the image: "main: left pane focused, right pane has no cursor" / "this branch: filled where the keyboard is, hollow where it is not".
- **4x nearest-neighbour crops** of the hard cases in one sheet (normal cell, inverse status bar, double-width glyph, blank cell), hollow above filled.
- Focus GIF with a caption explaining the setup: "a keystroke every 250 ms holds the blink off so the GIF shows only the focus change".
- A **transition strip, one tile per 8 ms**, with the time since the change under each tile (top row loses focus, bottom row gains it), plus the same at real 60 Hz cadence on glyphs.
- How section says what changed after looking: cubic ease-out left three invisible frames at the end, so it became quadratic. The comparison strip went in the media folder.

## Patterns worth copying

- **Captions are setup and instruction**: the input, the frame rate, and what to look at. ("Look at the bottom bar of faint blocks: a faint rainbow before, flat after.")
- **Stills first, then motion, then slowed motion, then crops**, from the easiest to read to the most detailed.
- **Main is always rendered**, never described, and the method is disclosed.
- **Honest readings of the images**, including "close to identical, and I am not going to claim otherwise".
- **Numbers with method and noise**: "within noise; other agents were building during the main run".
- **What you tried and dropped, and why**, which is what makes a reviewer trust the choice that shipped.
- **Not in this PR**, which draws the scope line before the reviewer has to ask.

## What to trim

The five bodies run 1,230 to 1,560 words. Their How and Verification sections are excellent reference material but a heavy read. The fix is **order and compression**, not deleting evidence:

- The top should be 1 or 2 plain paragraphs, not a `## Why` that runs four paragraphs followed by a `## What` of 6 bullets.
- Put images right after the summary. In #464 the first image comes after about 700 words. It should come after about 100.
- Keep one sentence per caption.
- In How, cut every bullet to its decision plus its reason. Implementation narration ("destructures the theme without `..`") belongs in code comments.
- Put long Verification inside `<details>`. Keep the headline results visible: byte-identical fixture, frame counts, tests passed.

### #476 rewritten in the target shape

```markdown
An unfocused terminal pane used to draw no cursor at all, so in a split you
couldn't tell which pane was live or where your typing would land when you came
back. The cursor also vanished whenever the window lost focus or the palette
was open. Now a pane without the keyboard draws the cursor as a 1 px outline in
the cell's cursor color, like Terminal, iTerm2, Ghostty, kitty and Alacritty.
It's a static marker: an unfocused pane schedules zero frames.

## Before and after

**Two panes, left focused.** On main the right pane shows no cursor at all. On this branch it's a hollow outline.
![before and after, dark](…/before-after-dark.png)

**The hard cells, at 4x.** Hollow on top, filled below: a normal cell, an inverse status bar, a double-width glyph, a blank cell.
<img src="…/crops-4x-dark.png" width="640" alt="4x crops">

**Focus moving.** 60 fps; a keystroke every 250 ms keeps the blink off, so only the focus change shows.
![focus moving](…/focus-dark.gif)

**Slowed down.** One tile per 8 ms since the change. The top pane's fill drains under a constant outline; the bottom pane's fills back in over 120 ms.
![transition in 8 ms steps](…/transition-8ms-steps-dark.png)

<details><summary>Light theme</summary>

![before and after, light](…/before-after-light.png)
![focus moving, light](…/focus-light.gif)
</details>

---

## How
- **Quadratic, not cubic, ease-out.** I tried the glide's cubic first; at 60 Hz its last three frames repaint a fill under 3% that nobody can see change. Quadratic over the same 120 ms makes every frame visibly different.
- **Border stroked inward, snapped to device pixels.** Cells are fractional (7.83 px wide), so the edges are rounded and the stroke kept inside the cell. Read-back shows exactly 2 device px per side at 2x, with neighbours untouched.
- **Starts from what is on screen.** Losing focus mid-blink drains from the dimmed opacity instead of popping to full first.
- **Double width.** On main the filled block covered half a CJK glyph. Both shapes now span the glyph.

## Verification
- Paint fixture with the pane focused: byte-identical to main.
- Unfocused pane: 0 frame requests at rest (a test asserts `simulate_next_frame` finds 0 callbacks); one focus change costs 8 frames, then rest.
- `cargo test --workspace`: 2,350 passed, 0 failed. fmt and clippy clean.
<details><summary>Bench and full test breakdown</summary>…</details>

## Not in this PR
- Bar and underline cursor shapes (DECSCUSR): the renderer only draws a block today.
```

About 400 words, with all the evidence still there.

## Brief template for delegating a visual PR

The orchestrator's per-PR prompt ended with a deliverables block like this one. Name the shots, the states, and the numbers:

```markdown
### Deliverables in the PR
- A before/after still of <scene> on main vs this branch, in <dark and light | phone and desktop>.
- A <4x crop | zoomed> sheet of <the edge cases: …>.
- A GIF of <the interaction>, and a slowed frame strip of <the transition> so the easing can be judged.
  Say what you tried and what you changed after looking.
- <Numbers>: <frames requested at rest | p95 latency | queries per request>, main vs branch, with method.
- Pixel diff vs main (expected: none outside <region>), fmt/lint/test results.
```

Also put the platform capture recipe in the brief (from `capture.md`), point it at this skill, and tell it to **measure the premise first and say plainly if it's weaker than stated**.
