# Composing media: the visual vocabulary

Each format answers a different reviewer question. Pick formats by question, not by habit.

| Question the reviewer has | Format | Tool |
|---|---|---|
| What changed? | **Before/after still**, same scene, stacked or side by side, caption bar on each panel | `compare.py` |
| Does it feel right at real speed? | **Real-speed GIF** of the interaction, 2–4 s, held last frame | `gif.sh` |
| Is the easing / timing right? | **Frame strip** with `+N ms` under each tile, and/or a **slow-motion GIF** (`--play-fps` 4–10x lower than capture) | `strip.py`, `gif.sh --play-fps` |
| Is main vs branch different in motion? | **Side-by-side GIF**, both builds driven by the same input script | `compare.py` on frame dirs, then `gif.sh` |
| Is it pixel-exact? Crisp? Aligned? | **Nearest-neighbour zoom crop** (4x) of the critical pixels, several cases in one sheet | `compare.py --crop --zoom 4` or `strip.py --labels` |
| Does it hold in every theme / size? | **Grid of the same shot** across light/dark, sizes, locales | `compare.py` (h then v) |
| Is the math right? (color, curves) | **Midpoint / swatch comparison**: approach A vs B at the same parameter | `compare.py` |
| What happens over time / at scale? | **Chart**: waterfall, distribution, series (see `backend.md`) | `chart.py` |

## Order in the body

Show the most convincing evidence first, the most detailed last:

1. Before/after still, so the reader sees the change in one glance.
2. Real-speed GIF, so they see how it feels.
3. Slowed GIF or frame strip, so they can judge the motion.
4. Zoom crops and theme/size grids, for the edge cases.
5. Charts and tables, which usually belong in Verification.

A PR with no motion stops after step 1 or 4. Don't pad it.

## Labels on the image

- Every panel gets a caption bar saying what the panel **shows**: `main: whole-row steps` and `this branch: follows the pixels`, not "before" and "after".
- Every strip tile gets its time relative to the input (`-8`, `0`, `+8 ms`) or the value that's changing (`95%`, `81%`, …), and in #459 both: `64%` over `100 ms`.
- A title line above a strip saying what to look at: `one glide at 120 Hz: every frame from the keystroke echo, cubic ease-out over 80 ms`.
- Use a mono or system font, muted ink, on a bar matching the theme. No arrows, emoji, stickers or brand colors. The image is evidence, not marketing.

## Sizes and budgets

- **Capture at 2x and display at about 1x.** GitHub renders images at up to roughly 900 px in the PR column. A 2x capture of a 450–1000 px region stays sharp.
- **Readable at 900 px.** Labels must survive that downscale. `strip.py` wraps rows at about 2000 px for this reason. Anything wider than about 2000 px gets its text shrunk to noise.
- **GIFs under about 4 MB** (GitHub accepts larger, but reviewers on slow connections see a blank box). Levers, in order: crop to the region that moves, shorten to one clean repetition, `--width` down, drop to 30 fps. `gif.sh` warns above 4 MB.
- **Hold the last frame about 1 s** (`gif.sh --hold`) so the loop reads as "action, result" rather than a seizure.
- **Start from rest.** Include a few frames before the input, so the change has a "before" inside the GIF itself.
- **Slow motion at 4–10x** for anything under 300 ms. 120 ms at real speed is 7 frames, which nobody can judge.
- **Nearest-neighbour** for any zoom that makes claims about pixels. Smooth scaling hides exactly what you're trying to show.
- Stills should be PNG. JPEG smears text and hairlines.

## Look at every image before shipping

Open each file with your image-reading tool and check:

- It shows what its caption says it shows, and the difference is visible at 900 px.
- Labels are legible and don't overlap content.
- Crops include the whole region of interest and nothing distracting.
- Panels line up (same crop box, same scale) so the eye compares like with like.
- Motion strips are monotonic where they should be, with no dead frames and no flash on the first or last frame.
- Nothing personal or secret is visible (real emails, tokens, customer names). Fixtures should make this impossible anyway.

When looking changes a decision (easing, duration, a color), say so in How: "the first version reused the cubic ease-out; at 60 Hz its last three frames repaint a fill under 3% that nobody can see change, so it's quadratic now". Those lines show the reviewer the work was judged, not just produced.

## Recipes

```sh
# stills: main above branch, dark, cropped to the pane
compare.py -o before-after-dark.png --crop 0,0,1520,500 \
  "main: right pane has no cursor" main-dark.png \
  "this branch: hollow where the keyboard is not" branch-dark.png

# 4x crops of the edge cases, labelled
compare.py --stack h --crop 120,300,200,340 --zoom 4 -o crops.png \
  "normal cell" normal.png "inverse cell" inverse.png "double width" wide.png

# side-by-side motion, then GIF at real speed and at 4x slow motion
compare.py --stack h -o side/ "main: snaps shut" frames_main/ "this branch: settles open" frames_branch/
gif.sh side/ real.gif --fps 60
gif.sh side/ slow.gif --fps 60 --play-fps 15

# frame strip: frames 6..24 of an 8 ms capture, input at frame 8
strip.py frames/ -o transition.png --range 6:24 --ms-per-frame 8 --t0 8 \
  --crop 300,180,420,240 --zoom 2 --title "focus leaves the top pane"
```
