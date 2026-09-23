# Synthetic fixtures: UI and data made for the PR

The reference PRs never screenshot someone's real session. Each one builds a small scene that exists only to show the change: a realistic terminal transcript, two panes side by side, a row of color swatches, a bar of block glyphs over a rainbow backdrop. That's why their images are so clear: every pixel on screen is there to be looked at.

## What makes a fixture good

1. **Realistic, not lorem ipsum.** Use content a real user would have: a `git diff --stat`, a test run with one failure, a cart with a 60-character product name, an inbox with unread and read items, a table with a null in it. Placeholder content hides the problems that real content exposes (wrapping, truncation, alignment, contrast).
2. **It explains itself where that's natural.** The diri fixtures filled the screen with text about the feature: test names like `cursor_focus::morph_ends_at_rest ... ok`, an agent line reading "The cursor is only drawn when focused. An outlined block keeps the insertion point visible in the other pane." The reviewer reads the explanation while looking at the evidence. Do this lightly, the way the real product would show it, and never with fake UI chrome.
3. **Every state and edge case in one frame.** Put the things the change must handle side by side so a single image proves them all: a normal cell, an inverse cell, a double-width glyph, a blank cell; an empty list, one item, overflow; short name, long name, RTL name; success, warning, error. The 4x crop sheet in #476 is exactly this.
4. **Deterministic.** Fixed data (checked in or generated from a seed), a fixed "now", a fixed size, no network. Running it twice must give byte-identical images, which is what makes a pixel diff against `main` meaningful.
5. **Stress where the change lives.** A scrolling PR gets a long list with sticky headers and a selection that spans rows. A color PR gets every palette color on every background (the swatch grid in #464). A performance PR gets the heavy case (1,000 rows, 50 open panes).
6. **Honest about exaggeration.** If you have to amplify an effect to make the mechanism visible (tint lowered from 0.95 to 0.55 so glass bleed shows), keep the real-coverage shot too and label the exaggerated one: **This is not what ships.**

## Where fixtures live, per stack

| Stack | Fixture seam |
|---|---|
| Next.js / React web | A dev-only route (`app/(dev)/pr/<feature>/page.tsx` with `if (process.env.NODE_ENV === 'production') notFound()`), a Storybook story, or the real page with `page.route` serving fixture JSON |
| Vue / Svelte / other web | Same: dev-only route, histoire/Storybook story, or intercepted API |
| iOS / macOS | DEBUG launch argument that loads fixture data and opens a screen, a SwiftUI `#Preview` with fixture models rendered via `ImageRenderer`, or snapshot tests |
| Android | Debug build flavor or intent extra; Compose `@Preview` rendered by Paparazzi/Roborazzi |
| React Native / Flutter | Dev-only deep link or launch env; Flutter golden tests |
| Custom renderer / engine | An ignored test that builds the scene and renders offscreen (diri's `tmp_shot.rs`, `theme_fade_frames.rs`) |
| Backend | Seeded database, recorded request set, deterministic load script (see `backend.md`) |

## Keep it or delete it

- **Delete** scratch fixtures before the final commit if they were only for this PR (diri's `tmp_shot.rs` was deleted).
- **Keep** a fixture when it's cheap and the next PR in the area will want it. Commit it as an ignored test or a dev-only route whose header documents the knobs and the exact command that produced the PR's media. `theme_fade_frames.rs` opens with the command, the env vars, and "`docs/screenshots/theme-crossfade` was made with it", which makes the media reproducible by anyone.
- Never ship fixture code in production paths. Gate it behind DEBUG, a dev-only route, or test-only compilation.
