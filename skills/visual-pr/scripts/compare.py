#!/usr/bin/env python3
"""Put two or more captures side by side (or stacked), each under a caption bar.

A caption says what the panel SHOWS, not just which build it is:
"main: right pane has no cursor", not "before".

Images:
  compare.py -o before-after.png \
      "main: right pane has no cursor" before.png \
      "this branch: hollow where the keyboard is not" after.png

Frame directories (for a side-by-side GIF): pass directories instead of
files. Frames are paired by sorted order, the output is a directory of
frame_%04d.png, and the shorter sequence holds its last frame.

  compare.py --stack h -o side/ "main" frames_main/ "branch" frames_branch/

Options:
  --stack v|h        vertical (default) or horizontal
  --crop x0,y0,x1,y1 crop every input first, in the input's pixels
  --zoom N           nearest-neighbour upscale after cropping (honest pixels)
  --scale F          smooth resample after cropping (e.g. 0.5 for a 2x capture)
  --font-size N      caption size in output pixels (default 22)
  --theme dark|light caption bar colors (default dark)
"""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
]
THEMES = {
    "dark": {"bar": (24, 24, 27), "text": (200, 200, 205), "gap": (40, 40, 44)},
    "light": {"bar": (242, 242, 245), "text": (60, 60, 67), "gap": (214, 214, 219)},
}


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def prepare(im, args):
    im = im.convert("RGB")
    if args.crop:
        im = im.crop(tuple(int(v) for v in args.crop.split(",")))
    if args.scale and args.scale != 1:
        im = im.resize((round(im.width * args.scale), round(im.height * args.scale)), Image.LANCZOS)
    if args.zoom and args.zoom != 1:
        im = im.resize((im.width * args.zoom, im.height * args.zoom), Image.NEAREST)
    return im


def compose(images, captions, args):
    colors = THEMES[args.theme]
    f = font(args.font_size)
    bar = round(args.font_size * 1.9)
    gap = 0 if args.stack == "v" else max(8, args.font_size // 2)
    w = max(i.width for i in images)
    h = max(i.height for i in images)
    if args.stack == "v":
        size = (w, len(images) * (h + bar) + (len(images) - 1) * gap)
    else:
        size = (len(images) * w + (len(images) - 1) * gap, h + bar)
    canvas = Image.new("RGB", size, colors["gap"])
    draw = ImageDraw.Draw(canvas)
    for k, (im, caption) in enumerate(zip(images, captions)):
        x, y = (0, k * (h + bar + gap)) if args.stack == "v" else (k * (w + gap), 0)
        panel_w = w
        draw.rectangle((x, y, x + panel_w - 1, y + bar - 1), fill=colors["bar"])
        draw.text((x + args.font_size // 2, y + (bar - args.font_size) // 2 - 1), caption, fill=colors["text"], font=f)
        # pad a short panel with its own corner color so it does not show a gap stripe
        pad = Image.new("RGB", (panel_w, h), im.getpixel((0, 0)))
        pad.paste(im, (0, 0))
        canvas.paste(pad, (x, y + bar))
    return canvas


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--stack", choices=["v", "h"], default="v")
    p.add_argument("--crop")
    p.add_argument("--zoom", type=int, default=1)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--font-size", type=int, default=22)
    p.add_argument("--theme", choices=list(THEMES), default="dark")
    p.add_argument("pairs", nargs="+", help='"caption" path, repeated')
    args = p.parse_args()
    if len(args.pairs) % 2:
        sys.exit("expected caption/path pairs")
    captions = args.pairs[0::2]
    paths = [Path(v) for v in args.pairs[1::2]]

    if all(path.is_dir() for path in paths):
        sequences = [sorted(path.glob("*.png")) for path in paths]
        if not all(sequences):
            sys.exit("a frame directory has no .png files")
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("frame_*.png"):
            old.unlink()
        n = max(len(s) for s in sequences)
        for i in range(n):
            frames = [prepare(Image.open(s[min(i, len(s) - 1)]), args) for s in sequences]
            compose(frames, captions, args).save(out / f"frame_{i:04d}.png")
        print(f"{out}: {n} frames")
    elif not any(path.is_dir() for path in paths):
        compose([prepare(Image.open(path), args) for path in paths], captions, args).save(args.out)
        print(args.out)
    else:
        sys.exit("pass either all image files or all frame directories")


if __name__ == "__main__":
    main()
