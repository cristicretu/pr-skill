# Getting media into the PR

There's no API for the drag-and-drop upload GitHub's web editor uses (`user-attachments`). An agent has to host the media in git and link it by URL.

## Where the media goes, in order

1. **The repo's own instructions win.** Check `AGENTS.md`, `CLAUDE.md` and `CONTRIBUTING.md` for a media rule (a branch name, a folder, "no binaries in the repo") and follow it exactly.
2. **An existing convention comes next.** If PRs in this repo already commit screenshots on the PR branch (`git log --all --oneline -- '*.png' '*.gif' | head`, or a folder like `docs/screenshots/`), do the same, in its own commit ("Add <feature> comparison media").
3. **Otherwise, use an orphan `pr-media` branch.** It never merges, so no binaries reach `main`. It works for forks and for PRs you didn't write, and it adds nothing to the PR's own history. This is the default.

Never add commits to someone else's PR branch just to host images.

### The orphan `pr-media` branch

```sh
git worktree add --detach ../pr-media
cd ../pr-media
git fetch origin pr-media && git checkout pr-media \
  || (git checkout --orphan pr-media && git rm -rfq .)
mkdir -p <feature-branch-name> && cp /path/to/media/* <feature-branch-name>/
git add . && git commit -m "Media for <feature-branch-name>" && git push -u origin pr-media
scripts/media-urls.sh <feature-branch-name> --check    # run inside ../pr-media
```

Name the files in descriptive kebab-case: `before-after-dark.png`, `focus-light.gif`, `transition-8ms-steps-dark.png`. Say in the PR that its media lives on `pr-media`, so nobody deletes the branch.

### Links

`scripts/media-urls.sh <dir> --check` prints one markdown image line per file. It refuses to print anything if HEAD isn't pushed, lists only files that commit contains, and with `--check` confirms that every file resolves. Public repos are checked over HTTP; private repos through the GitHub API.

| Repo | URL |
|---|---|
| Public | `https://raw.githubusercontent.com/<owner>/<repo>/<FULL_SHA>/<path>` |
| Private | `https://github.com/<owner>/<repo>/blob/<FULL_SHA>/<path>?raw=true` (renders for anyone who can read the repo; `raw.githubusercontent.com` would 404 for them) |

**Why the SHA and not the branch name:** a branch URL changes when someone pushes to it, and breaks if the branch is deleted. A pinned SHA always shows the same file. On `pr-media` the SHA stays reachable as long as the branch exists; on a PR branch, GitHub keeps it through `refs/pull/<n>/head`.

**Don't use relative paths** (`![](docs/screenshots/x.png)`). They don't resolve in PR descriptions.

## Video

GitHub plays video only from its own upload endpoint, not from a repo URL. A linked `.mp4` or `.mov` shows up as a download link. So:

- Use a **GIF** for anything under about 10 s. That covers nearly every UI change.
- For a long flow (a 30 s onboarding), commit an MP4, link it ("full flow, 34 s, mp4"), and still embed a GIF of the key 3 s. If a human is around, they can drag the MP4 into the PR editor to get an inline player.

## Formats

- **PNG** for stills, **GIF** for motion.
- **Mermaid** diagrams go inline as ```` ```mermaid ```` blocks, which GitHub renders natively. No image needed, and reviewers can diff them.
- Avoid SVG from raw URLs: it may be served as text or blocked. Render it to PNG instead.
- **Tables** go in markdown, not screenshots of tables.

## Final check

```sh
gh pr view <n> --json body --jq .body | grep -oE 'https://[^)]+\.(png|gif|jpe?g)[^)]*'
```

Every URL should contain a full 40-character SHA that's on the remote. `media-urls.sh --check` verifies them; for a spot check, `curl -sI` a public URL, or `gh api repos/<owner>/<repo>/contents/<path>?ref=<sha>` a private one. If you can open the PR in a browser, look at it. The page the reviewer sees is what you actually delivered.
