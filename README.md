# visual-pr

An agent skill for pull requests a reviewer understands in one scroll:

1. **A short, human summary** (120 words at most) of what was wrong and what's different now.
2. **Evidence made for the PR**, laid out as titled figures: before/after stills in `main | this branch` tables, real-speed and slowed-down GIFs, frame strips with `+N ms` labels, and zoomed crops of edge cases. Every figure has a caption naming the input, what changed, and where to look.
3. **Edge cases**, scaled to the risk: a table of what else the change could break (existing flows through the changed code, mid-session transitions, hover and focus, long text, RTL, permissions, concurrency) and how each was checked.
4. **The details** for whoever wants them: How (decisions and rejected alternatives), Verification (real numbers), Not in this PR.

It works for web (Next.js, React, anything in a browser), iOS, Android, React Native, Flutter, desktop, custom renderers and CLIs. It also works for backend changes: query waterfalls, latency distributions, worker lanes with a replay GIF, fault-injection timelines, and small diagrams when structure is the point. When a backend change has an effect a user can see, it shows both layers of the same action.

## Install

```sh
npx skills add cristicretu/pr-skill
```

Works with Claude Code, Codex, Cursor, OpenCode and [the other agents the `skills` CLI supports](https://github.com/vercel-labs/skills#supported-agents).

Claude Code plugin:

```
/plugin marketplace add cristicretu/pr-skill
/plugin install pr-skill@pr-skill
```

Or by hand: copy or symlink `skills/visual-pr` into your agent's skills directory (for Claude Code, `~/.claude/skills/visual-pr`).

Then ask your agent to open a PR, or to rewrite a PR's description, and it will use the skill.

## Examples

PRs written by agents given only a problem statement and this skill:

- [Cart drawer slides in and out; total stays beside Checkout](https://github.com/cristicretu/pr-skill-playground/pull/1): a side-by-side GIF at real speed and at 4x slow motion, captured on a frozen clock, plus a `main | branch` footer table at 375 px, with dark theme and 320 px folded under a `<details>`. Verification includes a per-frame `translateX` table.
- [Batch customer lookups](https://github.com/cristicretu/pr-skill-playground/pull/2): a query waterfall of 21 sequential queries against 2 on one time axis, plus p50/p95/p99 latency (337 ms → 33 ms) and a byte-identical response check.

The skill is distilled from five PRs on [cristicretu/diri](https://github.com/cristicretu/diri) ([#459](https://github.com/cristicretu/diri/pull/459), [#460](https://github.com/cristicretu/diri/pull/460), [#464](https://github.com/cristicretu/diri/pull/464), [#465](https://github.com/cristicretu/diri/pull/465), [#476](https://github.com/cristicretu/diri/pull/476)), which `references/examples.md` walks through.

## What's inside

```
skills/visual-pr/
  SKILL.md                 workflow, body shape, captions, layout, backend
  references/
    capture.md             stills and stepped motion per platform
    fixtures.md            synthetic scenes and data made for the PR
    media.md               which visual answers which question; sizes, labels, budgets
    backend.md             making server, data and infra changes visible
    edge-cases.md          blast radius, mid-session transitions, frontend/backend checklists
    hosting.md             SHA-pinned image URLs, private repos, media branch, video
    examples.md            the reference PRs walked through, and a rewrite in the target shape
  scripts/
    web-frames.mjs         Playwright: stills and frames on a frozen, stepped clock (any web framework)
    compare.py             labeled before/after panels (images or frame dirs)
    strip.py               frame strip with +N ms labels, crop, nearest-neighbour zoom
    gif.sh                 ffmpeg palette GIF, slow motion, held last frame, size check
    chart.py               waterfall / lanes (+ replay frames), latency ECDF, series with fault band
    media-urls.sh          commit-pinned markdown image lines, checked against the remote
```

## Requirements

- `git` and `gh` (authenticated)
- Python 3 with Pillow; matplotlib for `chart.py`
- ffmpeg
- For web capture: Node and Playwright in the target project (`pnpm add -D playwright && pnpm exec playwright install chromium`)

## License

MIT
