# Getting media into the PR

There's no API for the drag-and-drop upload GitHub's web editor uses (`user-attachments`). An agent has to host the media in git and link it by URL.

## Default for a PR you're opening: commit it on the PR branch, link it by commit SHA

(Updating an existing PR's description, or a PR from a fork? Skip to the orphan media branch below. Never add commits to a branch just to host images.)

1. Put the files under the repo's existing media convention. Check first (`git ls-files | grep -iE '\.(png|gif)$' | head`). If there isn't one, use `docs/screenshots/<feature>/`, with descriptive kebab-case names: `before-after-dark.png`, `focus-light.gif`, `transition-8ms-steps-dark.png`.
2. Commit them in their own commit (e.g. "Add <feature> comparison media"), so a reviewer can skip it and it can be dropped later.
3. Push.
4. Get the markdown lines:
   ```sh
   scripts/media-urls.sh docs/screenshots/<feature> --check
   ```
   It refuses to print anything if HEAD isn't pushed, lists only files that commit actually contains, and with `--check` fetches every URL.
5. Write or update the body with them: `gh pr create --body-file body.md`, or `gh pr edit <n> --body-file body.md`.

URL forms:

| Repo | URL |
|---|---|
| Public | `https://raw.githubusercontent.com/<owner>/<repo>/<FULL_SHA>/<path>` |
| Private | `https://github.com/<owner>/<repo>/blob/<FULL_SHA>/<path>?raw=true` (renders for anyone who can read the repo; `raw.githubusercontent.com` would 404 for them) |

**Why the SHA and not the branch name:** a branch URL breaks when the branch is deleted after merge, and it changes if someone force-pushes. A SHA from the PR stays reachable through the PR's `refs/pull/<n>/head`, so the images outlive the branch.

**Don't use relative paths** (`![](docs/screenshots/x.png)`). They don't resolve in PR descriptions.

## Orphan media branch: existing PRs, forks, and repos that shouldn't get binaries in the main history

Committing media on the branch means it merges into `main` (the diri PRs did this, which is fine for a small repo with a `docs/screenshots` convention). If the repo is large, strict about binaries, or has no such convention, use a dedicated orphan branch that never merges:

```sh
git worktree add --detach ../pr-media
cd ../pr-media
git fetch origin pr-media && git checkout pr-media \
  || (git checkout --orphan pr-media && git rm -rfq .)
mkdir -p <feature-branch-name> && cp /path/to/media/* <feature-branch-name>/
git add . && git commit -m "Media for <feature-branch-name>" && git push -u origin pr-media
scripts/media-urls.sh <feature-branch-name> --check    # run inside ../pr-media
```

Say in the PR which branch the media lives on, so nobody deletes it.

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

Every URL should contain a full 40-character SHA that's on the remote. For public repos, `curl -sI` each one and expect a 200. If you can open the PR in a browser, look at it. The page the reviewer sees is what you actually delivered.
