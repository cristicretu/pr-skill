---
name: visual-pr
description: Write pull requests a reviewer can understand in one scroll. A short human summary, then before/after stills, GIFs and slowed-down frame strips made for the PR from synthetic fixtures, each with a caption naming the state change, then the details. Use whenever you open a PR, write or rewrite a PR description, or are asked for "before/after", screenshots, a GIF or a demo of a change. It matters most for UI, animation, rendering, color, layout, performance and UX changes, and it still applies to backend work, where the visuals are diagrams, tables and output diffs.
---

# Visual PRs

A reviewer should understand what changed and see that it works before reading a single line of the How. Words alone don't do that. Evidence you made for the PR does: the same input rendered on `main` and on the branch, the motion slowed down until the easing can be judged, the edge cases cropped and zoomed in, and the numbers measured.

The reference PRs this skill is distilled from are cristicretu/diri #459, #460, #464, #465 and #476. `references/examples.md` walks through what each one did.

## The shape of the body

```
<1–2 paragraphs, plain words: what was wrong or missing, as a user feels it,
 and what is different now. Nothing else above the first figure.>

## Before and after          (or name what is shown: "Hovering a session")

**Cross-project hover.** <caption: the input, what differs, where to look>

| main | this branch |
|---|---|
| <img src="…/main-dark.png" alt="…"> | <img src="…/branch-dark.png" alt="…"> |

**Moving the pointer.** <caption>
![…](one composited main|branch GIF)

**Slowed down.** <caption: "one tile per 8 ms; top row loses focus, bottom gains it">
![…](frame strip)

<details><summary>Light theme</summary> …same table… </details>

---

## How            (the decisions that aren't obvious, and what you tried and dropped)
## Verification   (real numbers and commands; paste results, not claims)
## Not in this PR (the scope you drew, and anything you noticed but left)
```

Rules for each part:

1. **Summary (max 2 paragraphs).** Write it the way you'd explain the change to a colleague at their desk. Name the concrete symptom ("under a slow drag the text sat still for 15 px of finger travel and then jumped"), not a category ("improves scrolling"). If you checked the premise before building and it turned out weaker than expected, say so here. Being honest about that earns more trust than anything else in the PR. No headers, no bullets, no file names. Hard cap: **120 words across both paragraphs**. Count them. Write for someone who hasn't read the issue or the code: say what a user saw and what they see now. Internal names (lock types, function names, error codes) go in How, unless one of them is the symptom itself.
2. **Visuals, as figures.** Group them under one heading straight after the summary. Each figure gets a **bold 2–5 word title**, then one caption sentence saying what input was replayed, what differs, and where to look, then the media. The caption explains the state change so the image doesn't have to be decoded. See "Captions" and "Layout" below.
3. **Details, after the visuals.** Use only the sections that add something. How covers the non-obvious decisions and the alternatives you rejected, with the reason for each. Verification gives measured results. Not in this PR marks the scope. If the details run long, put Verification inside `<details><summary>Verification</summary>…</details>` so the page stays scannable.
4. **Optional sections** that earn their place when they apply: *Review first* (the 2–4 spots where you're least sure, which also tells the reviewer where to start), *Merge notes* (conflicts with open PRs), and *Tests changed, and why* (every existing test you modified, with the reason).

Length. The reference PRs run to about 1,300 words, which is too long. Aim for a summary under 120 words, captions of one sentence, and bullets of one or two lines. Cut any sentence that repeats what an image already shows. Keep the numbers and the rejected alternatives, because those are the parts reviewers can't get anywhere else.

## Every visual has to earn its place

Before adding a visual, write down the reviewer question it answers ("does the naive fix also work?", "does the easing overshoot?"). If you can't, cut it. If deleting it loses nothing the text already says, delete it. Two strong figures beat six adequate ones.

- A **diagram** is only for structure that prose handles badly: a cycle (a deadlock is a 3-node wait-for loop, not a 10-message sequence diagram), a race interleaving, or a topology that changed. Use the smallest form that shows it. Don't draw an "after" diagram when the fix is "that edge is gone". Say it in one sentence.
- **Raw output** (`ps`, logs, EXPLAIN) goes in only when a claim rests on it, trimmed to the lines that matter, usually inline or folded.
- A **variant** that repeats a point (the light theme when dark already shows it, a second device) goes in a `<details>` block, unless the variant is the point.

## Layout: figures, not pasted images

- **Pairs go in a table.** Column headers replace the burned-in labels, and the images line up. `| main | this branch |`, one row per state or theme, with a first label column if there are several rows. Upload the two panels as separate images for this. It suits narrow subjects (a sidebar, a phone screen, a component, a crop), since each column renders about 440 px wide.
- **Several items described by the same attributes get a table, not bullets.** Examples: three or more flakes with root cause and fix, endpoints with before/after latency, themes with contrast ratios. If you catch yourself writing the same sentence shape three times, it's a table.
- **Wide subjects** (a full window, a terminal, a chart) get one stacked composite at full width. A table would shrink them until they're unreadable.
- **Motion comparisons stay one composited GIF.** Two GIFs in two cells don't start in sync.
- **Never two images in a row with no text between them**, except inside a table.
- A `---` between the figures and `## How` separates what to look at from what to read.
- Use `<img src="…" width="420">` when an image renders larger than its information deserves (a small crop captured at 2x).

## Captions that explain the state change

A good caption answers three things: **what input** produced this, **what differs** between the panels or frames, and **where to look**.

| Weak | Strong |
|---|---|
| Before and after | Same scripted fling replayed on main (top) and this branch (bottom): main holds still, then jumps a row |
| Checkout page | Cart with 40 items and a 60-character product name, iPhone SE width: the total used to wrap under the button, now it stays on one line |
| GIF of the animation | Opening the sheet, then dragging it halfway and letting go. On main it snaps shut; now it settles back open |
| Frame strip | Slowed down, one tile per 8 ms, times since the click. Watch the badge: it scales from 0.9, never from 0 |
| Loading state | Network throttled to 3G: the skeleton now holds the exact layout of the loaded list, so nothing shifts when data arrives |
| Dark mode screenshot | Look at the divider under the header: invisible on main in dark mode, a 1 px line now |

Put labels on the images too. Each panel gets a caption bar saying what it shows (`main: total wraps under the button` / `this branch: one line at 320 px`), and each strip tile gets its time (`+16 ms`) or value (`64%`). A reader skimming only the images should still get the story.

When a visual doesn't show much, say so plainly: "the before/after transcripts are close to identical, and I am not going to claim otherwise." If a fixture exaggerates something to make the mechanism visible, label it in bold: **This is not what ships.**

## Workflow

Do this while you build, not after. The frames are also how you judge your own work. The reference agents found real bugs (a progress bar turning pink, yellow drifting olive, invisible final animation frames) only because they looked at them.

1. **Plan the shots** as soon as the change is understood. List the states and transitions a reviewer needs to see: before vs after, every state involved (focused/unfocused, empty/full, light/dark), the transition between states, and the edge cases (wide glyphs, long text, inverse colors, error state, small screen). Check the premise first: render `main` and confirm the problem looks like you were told it does.
2. **Build a synthetic fixture** that is realistic and deterministic. See `references/fixtures.md`. Real-looking content (a transcript, a diff, a list with long names), fixed data, fixed size, and content that describes the feature itself where that's natural.
3. **Capture deterministically.** Freeze or fake the clock and step it frame by frame, so every frame is exactly reproducible. Screen-record wall-clock time only when stepping is impossible, and say so in the caption. Render `main` from the same fixture and input script: a second worktree on another port or simulator, or the branch with the feature switched off (say which). `references/capture.md` has recipes for web and Next.js (Playwright fake clock, Web Animations scrubbing), iOS (simctl, status-bar override, Core Animation scrubbing, ImageRenderer), Android, React Native, Electron and desktop, custom renderers, and CLIs.
4. **Compose** with the bundled scripts (Python 3 + Pillow, ffmpeg; matplotlib for charts; Node + Playwright for web):
   - `scripts/web-frames.mjs`: web stills and stepped animation frames on a frozen clock, for any framework, with `--probe` to log a value per frame.
   - `scripts/compare.py`: labeled before/after panels, stacked or side by side. Pass frame directories instead of files to get a side-by-side GIF.
   - `scripts/strip.py`: frame strip with `+N ms` labels, a crop of the region that moves, and nearest-neighbour zoom.
   - `scripts/gif.sh`: palette-optimized GIF with slow-motion playback, a held last frame, and a warning over 4 MB.
   - `scripts/chart.py`: backend charts, main vs branch on one scale. Trace waterfalls and worker lanes (plus a replay GIF), latency distributions, series with a shaded fault window.
   Details and budgets are in `references/media.md`.
5. **Look at every image** with your image-reading tool before shipping it. Check it shows what the caption claims, the labels are readable at about 900 px wide, nothing is cropped wrong, and the motion reads the way you intended. If you changed something after looking (an easing, a duration, an opacity), put that in How. It's some of the most useful content in the PR.
6. **Host the media** by committing it under the repo's media convention (default `docs/screenshots/<feature>/`), pushing, and referencing it with a URL pinned to the commit SHA. Run `scripts/media-urls.sh docs/screenshots/<feature> --check` to print the markdown lines and confirm they resolve. See `references/hosting.md` for private repos, orphan media branches, and why you shouldn't use mp4. **If you're updating the description of an existing PR (yours or anyone's), don't add commits to its branch.** Push the media to the orphan `pr-media` branch instead, so the PR's code history stays exactly what the author pushed.
7. **Write the body** to a file only you use (`body=$(mktemp -t pr-<number>-body.XXXX)`). Other agents may share your scratch directory, and a shared `body.md` can end up posting one PR's description on another. Before posting, check that the file's first line is the summary for *this* change. Then create the PR with `gh pr create --body-file "$body"`, or update it with `gh pr edit <n> --body-file "$body"` if the media commit came later. Afterwards, run `gh pr view <n> --json title,body` and confirm the posted body belongs to that PR and every image URL points at a pushed SHA.

## Backend and full-stack changes

A backend PR has to **make a screen for the behavior**, with the same imagination as a UI PR. The equivalent of a synthetic UI is a throwaway visualization of real data from a scripted run against `main` and the branch, drawn on one scale:

- **Fewer or faster calls**: a trace waterfall, 14 stacked queries above, 2 below.
- **Latency**: an ECDF with p50/p95/p99, from the same load script on both builds.
- **Concurrency, queues, locks**: worker lanes, plus a replay GIF where a "now" line sweeps across and jobs visibly queue on main and run in parallel on the branch.
- **Resilience**: a fault-injection timeline with the outage shaded. In-flight requests pile up on main and fail fast on the branch.
- **Memory/CPU**: soak-test series and flame graphs. **Queries**: EXPLAIN before/after with the changed node called out.
- **Contracts and data**: request/response or sample rows before/after in a `diff` block, and an ER diagram for migrations.
- **Flows and state machines**: Mermaid sequence and state diagrams of the real participants, before and after.
- When none of these fit, build a **tiny single-file visualizer** (a token bucket filling, a queue draining, replicas converging) fed by the real code's event log, and capture it like any UI.

For **full-stack** changes, show one user action at both layers: the UI GIF (the spinner lasts 1.4 s on main and 0.2 s here) above the trace waterfall of the request that click fired, with one caption tying them together. The full catalog with data-collection recipes is in `references/backend.md`.

## Verification that reads as evidence

When you're describing someone else's PR, keep **what you ran** apart from **what the author reported** ("`cargo test --workspace` passed (author's run); I re-ran the three new tests on `b1039b3d`").


Write results, not claims: "1616 passed, 0 failed, 45 ignored" rather than "tests pass". Name any flaky test and say how you checked it. For visual changes, the strongest proof is a **byte-identical** comparison against `main` for everything that shouldn't change (pixel fixture dumps compared with `cmp`), plus an exact count of the pixels that did change and why. For performance, give the baseline, the branch result, the noise level, and what the machine was doing at the time ("other agents were building during the main run"). Never claim a result you didn't see.

## Delegating PRs to other agents

If you're orchestrating agents that each open a PR, give every one of them this skill, a brief with the repo's capture recipe, and the specific shots its PR must contain. Ask for the shots by name ("a before/after of two panes in dark and light, a 4x crop on an inverse cell, a GIF of focus moving, a slowed strip of the transition"). `references/examples.md` ends with the deliverables block from the brief that produced the reference PRs.

## Reference files

| File | Read it when |
|---|---|
| `references/capture.md` | Capturing stills or motion on web/Next.js, iOS, Android, React Native/Flutter, desktop, custom renderers, CLI |
| `references/fixtures.md` | Building the synthetic scene or data the shots are taken of |
| `references/media.md` | Choosing formats, labels, sizes, GIF budgets, and the composing recipes |
| `references/backend.md` | The change is server-side, data, infra, or full-stack |
| `references/hosting.md` | Getting images into the PR body (SHA-pinned URLs, private repos, orphan media branch, video) |
| `references/examples.md` | Seeing the reference PRs dissected, a rewritten body in the target shape, and a delegation brief |
