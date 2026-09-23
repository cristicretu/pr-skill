#!/usr/bin/env python3
"""Lay frames out in a row with a time label under each, so motion can be
judged from a still: easing, overshoot, dead frames, flicker.

  strip.py frames/ -o transition.png --crop 300,180,420,240 --zoom 2 \
      --range 6:24 --ms-per-frame 8 --t0 8 --title "focus leaves the top pane"

Options:
  --range A:B[:S]    frame indexes to use (python slice over sorted frames)
  --crop x0,y0,x1,y1 crop each frame (input pixels) to the region that moves
  --zoom N           nearest-neighbour upscale so pixel steps stay honest
  --ms-per-frame F   capture interval; labels become "+N ms" relative to --t0
  --t0 N             frame index that is time zero (the input / state change)
  --labels a,b,c     explicit per-tile labels instead of times ("|" = new line)
  --title TEXT       one line above the strip saying what to look at
  --wrap N           start a new row every N tiles (default: keep rows ~2000 px)
"""
import argparse
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("frames", help="directory of frame_*.png (sorted by name)")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--range", default=":")
    p.add_argument("--crop")
    p.add_argument("--zoom", type=int, default=1)
    p.add_argument("--ms-per-frame", type=float)
    p.add_argument("--t0", type=int, default=0)
    p.add_argument("--labels")
    p.add_argument("--title")
    p.add_argument("--wrap", type=int, default=0)
    p.add_argument("--font-size", type=int, default=18)
    args = p.parse_args()

    files = sorted(Path(args.frames).glob("*.png"))
    parts = [int(v) if v else None for v in (args.range.split(":") + [""])[:3]]
    indexes = list(range(len(files)))[slice(*parts)]
    if not indexes:
        raise SystemExit("no frames selected")

    tiles = []
    for i in indexes:
        im = Image.open(files[i]).convert("RGB")
        if args.crop:
            im = im.crop(tuple(int(v) for v in args.crop.split(",")))
        if args.zoom != 1:
            im = im.resize((im.width * args.zoom, im.height * args.zoom), Image.NEAREST)
        tiles.append(im)

    if args.labels:
        labels = [s.replace("|", "\n") for s in args.labels.split(",")]
    elif args.ms_per_frame:
        labels = []
        for i in indexes:
            t = (i - args.t0) * args.ms_per_frame
            labels.append(f"{t:+.0f} ms" if t else "0 ms")
    else:
        labels = [str(i) for i in indexes]

    f = font(args.font_size)
    bg = tiles[0].getpixel((0, 0))
    fg = (140, 140, 145)
    pad = 8
    w = max(t.width for t in tiles)
    h = max(t.height for t in tiles)
    lines = max(label.count("\n") + 1 for label in labels)
    label_h = lines * round(args.font_size * 1.3) + pad
    title_h = round(args.font_size * 1.9) if args.title else 0
    # GitHub shows images about 900 px wide; a wider sheet shrinks its labels
    # to nothing, so wrap at ~2000 px (a 2x capture shown at 1x) by default.
    per_row = args.wrap or max(1, min(len(tiles), 2000 // (w + pad)))
    rows = (len(tiles) + per_row - 1) // per_row
    sheet = Image.new(
        "RGB",
        (pad + per_row * (w + pad), title_h + pad + rows * (h + label_h + pad)),
        bg,
    )
    d = ImageDraw.Draw(sheet)
    if args.title:
        d.text((pad, pad), args.title, fill=(200, 200, 205), font=f)
    for k, (tile, label) in enumerate(zip(tiles, labels)):
        r, c = divmod(k, per_row)
        x = pad + c * (w + pad)
        y = title_h + pad + r * (h + label_h + pad)
        sheet.paste(tile, (x, y))
        d.multiline_text((x, y + h + pad // 2), label, fill=fg, font=f, spacing=2)
    sheet.save(args.out)
    print(f"{args.out}: {len(tiles)} tiles, {sheet.width}x{sheet.height}")


if __name__ == "__main__":
    main()
