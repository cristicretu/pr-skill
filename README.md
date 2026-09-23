# pr-skill

A skill that teaches coding agents to open pull requests a reviewer understands in one scroll:

- a short, human summary at the top,
- then before/after stills, real-speed GIFs, slowed-down frame strips and zoomed crops, rendered from synthetic fixtures made for the PR, each with a caption that explains the state change,
- then the details (How, Verification, Not in this PR) for whoever wants them.

It works for web (Next.js, React, Vue, anything in a browser), iOS, Android, React Native and Flutter, desktop, custom renderers, CLIs, and backend work. For backend changes it turns behavior into visuals: trace waterfalls, latency curves, worker lanes with a replay GIF, fault-injection timelines, and before/after sequence diagrams.

It's distilled from five agent-written PRs on [cristicretu/diri](https://github.com/cristicretu/diri): [#459](https://github.com/cristicretu/diri/pull/459), [#460](https://github.com/cristicretu/diri/pull/460), [#464](https://github.com/cristicretu/diri/pull/464), [#465](https://github.com/cristicretu/diri/pull/465), [#476](https://github.com/cristicretu/diri/pull/476), and the brief that produced them. `skills/visual-pr/references/examples.md` dissects them.

## Layout

```
skills/visual-pr/
  SKILL.md                 the workflow, body shape, caption rules
  references/
    capture.md             stills and stepped motion per platform
    fixtures.md            synthetic scenes and data made for the PR
    media.md               which visual answers which question; sizes, labels, budgets
    backend.md             making server, data and infra changes visible
    hosting.md             SHA-pinned image URLs, private repos, media branch, video
    examples.md            the reference PRs annotated, a rewrite in the target shape
  scripts/
    web-frames.mjs         Playwright: stills + frames on a frozen, stepped clock
    compare.py             labeled before/after panels (images or frame dirs)
    strip.py               frame strip with +N ms labels, crop, nearest zoom
    gif.sh                 ffmpeg palette GIF, slow motion, held last frame, size check
    chart.py               waterfall / lanes (+ replay frames), latency ECDF, series
    media-urls.sh          commit-pinned markdown image lines, verified against the remote
```

Requirements: Python 3 with Pillow (and matplotlib for `chart.py`), ffmpeg, `gh`. For web capture, Playwright in the target project (`pnpm add -D playwright`).

## Install

Claude Code, personal skill:

```sh
ln -s "$PWD/skills/visual-pr" ~/.claude/skills/visual-pr
```

Claude Code plugin (this repo is also a one-plugin marketplace):

```
/plugin marketplace add <path-or-git-url-of-this-repo>
/plugin install pr-skill@pr-skill
```

Other agents (Codex, Cursor, etc.): copy or symlink `skills/visual-pr` into that agent's skills directory, or point the agent at `skills/visual-pr/SKILL.md`.
