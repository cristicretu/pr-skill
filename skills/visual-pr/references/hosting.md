# Getting media into the PR

Attach it, the same way pasting a screenshot into GitHub does. The file is uploaded to GitHub's attachment storage (`github.com/user-attachments/assets/…`), **nothing is committed**, and on a private repo only people who can read the repo can see it.

## Order of preference

1. **The repo's own instructions win.** Check `AGENTS.md`, `CLAUDE.md` and `CONTRIBUTING.md` for a media rule and follow it.
2. **`gh pr create/edit --attach`** (gh ≥ 2.99, a repo you can push to). This is the default.
3. **Fallbacks**, only when `--attach` can't be used (older gh you can't upgrade, a repo you can only read, CI with the Actions `GITHUB_TOKEN`): the [`gh-image`](https://github.com/drogers0/gh-image) extension (`gh image file.png` prints an attachment link), or, if the repo allows committed media, an orphan `pr-media` branch (see the end of this file).

Never commit images to the PR branch unless the repo already does that on purpose, and never add commits to someone else's PR branch to host images.

## Attaching (the default)

Check the version first: `gh --version` (upgrade with `brew upgrade gh` or your package manager if it's below 2.99).

1. Keep the media in a scratch folder next to the body file, with descriptive names: `before-after-dark.png`, `open-close-slow-4x.gif`, `footer-375-main.png`.
2. In the body, reference each file by a **relative path with markdown image syntax**:
   ```markdown
   **Opening the cart.** Same script on both builds, played at real speed.
   ![main vs branch, opening and closing the cart](./open-close.gif)

   | main | this branch |
   |---|---|
   | ![main: total wraps](./footer-375-main.png) | ![branch: one line](./footer-375-branch.png) |
   ```
3. Pass every file with `--attach`. gh uploads each one and rewrites the matching `./path` to its attachment URL:
   ```sh
   cd "$media_dir"
   gh pr create --title "…" --body-file "$body" \
     --attach ./open-close.gif --attach ./footer-375-main.png --attach ./footer-375-branch.png
   # or, for an existing PR:
   gh pr edit <n> --body-file "$body" --attach ./open-close.gif …
   ```
4. Check the result: `scripts/check-body.sh <n>`. It fails if any `./` reference was left unrewritten, or if an attachment doesn't load.

What `--attach` does and doesn't do (tested):

- `![alt](./file.png)` is rewritten anywhere in the body, **including inside table cells**.
- `<img src="./file.png">` is **not** rewritten. The file is appended at the bottom of the body instead. Use markdown image syntax for everything you attach.
- A file passed with `--attach` but never referenced is appended at the end of the body. Reference every file you attach.
- Alt text comes from the reference (`![this alt](./x.png)`), or from `--attach './x.png#alt text'` when appended.
- Up to 50 files per command. Images (PNG, JPEG, GIF, WebP…) and videos (MP4, MOV) are accepted. Videos render as an inline player.
- Attachment links need a signed-in viewer. An anonymous `curl` gets 404, and that's expected. `check-body.sh` fetches them with your gh token.

**Need a fixed display width** (a small crop captured at 2x)? After attaching, edit the posted body: replace `![alt](https://github.com/user-attachments/assets/…)` with `<img src="https://github.com/user-attachments/assets/…" width="420" alt="alt">`, then run `gh pr edit <n> --body-file` again without `--attach`. The URL is already uploaded, so a plain `<img>` works.

## Video

With `--attach`, MP4 and MOV render as an inline player. GIF is still better for anything under about 10 s, because it loops and plays without a click, which is what a before/after needs. Use a video for long flows (a 30 s onboarding), and still put a GIF of the key 3 s above it.

## Formats

- **PNG** for stills, **GIF** for short motion.
- **Mermaid** diagrams go inline as ```` ```mermaid ```` blocks, which GitHub renders natively. No image needed.
- Render SVG to PNG before attaching.
- **Tables** go in markdown, not screenshots of tables.

## Fallback: the orphan `pr-media` branch

Only when `--attach` can't be used **and** the repo allows committed media. It never merges, so no binaries reach `main`.

```sh
git worktree add --detach ../pr-media
cd ../pr-media
git fetch origin pr-media && git checkout pr-media \
  || (git checkout --orphan pr-media && git rm -rfq .)
mkdir -p <feature-branch-name> && cp /path/to/media/* <feature-branch-name>/
git add . && git commit -m "Media for <feature-branch-name>" && git push -u origin pr-media
scripts/media-urls.sh <feature-branch-name> --check    # prints SHA-pinned markdown lines
```

URLs are pinned to the commit SHA, so they never change. For public repos they're `raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>`; for private ones, `github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true`. Say in the PR that its media lives on `pr-media`, so nobody deletes the branch.

## Final check

Run `scripts/check-body.sh <pr-number>`. If you can open the PR in a browser, look at it too: the page the reviewer sees is what you actually delivered.
