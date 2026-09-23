#!/usr/bin/env bash
# Encode a directory of frame_%04d.png into a GIF GitHub will play inline.
#
#   gif.sh frames/ out.gif [--fps 60] [--play-fps N] [--width W] [--hold 1.0] [--crop w:h:x:y]
#
# --fps       rate the frames were captured at (default 60)
# --play-fps  rate to play them at; lower than --fps is slow motion
#             (captured at 60, played at 15 = 4x slower). Default: --fps.
#             GIF delays are in centiseconds, so rates above 50 get rounded.
# --width     output width in px. Default: the input width, capped at 1000 px
#             (GitHub's column is ~900; wider only costs bytes). A 2x capture
#             of a narrow region stays sharp, and side-by-side panels stay
#             readable. Use 0 to keep the input size exactly.
# --hold      seconds to hold the last frame so the loop reads (default 1.0)
# --crop      ffmpeg crop before scaling, w:h:x:y in input pixels
#
# Warns when the file is over 4 MB: crop tighter, shorten, lower --width,
# or drop to 30 fps rather than hoping the reviewer waits for it.
set -euo pipefail

src=${1:?frames dir}; out=${2:?output gif}; shift 2
fps=60; play=""; width=""; hold=1.0; crop=""
while [ $# -gt 0 ]; do
  case $1 in
    --fps) fps=$2; shift 2 ;;
    --play-fps) play=$2; shift 2 ;;
    --width) width=$2; shift 2 ;;
    --hold) hold=$2; shift 2 ;;
    --crop) crop=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
play=${play:-$fps}

first=$(ls "$src" | grep -E '^frame_[0-9]{4}\.png$' | sort | head -1)
[ -n "$first" ] || { echo "no frame_%04d.png in $src" >&2; exit 1; }
start=$(echo "$first" | sed -E 's/frame_0*([0-9]+)\.png/\1/')

filters=""
[ -n "$crop" ] && filters="crop=$crop,"
if [ -z "$width" ]; then filters+="scale='min(iw,1000)':-2:flags=lanczos,"
elif [ "$width" != 0 ]; then filters+="scale=$width:-1:flags=lanczos,"; fi
filters+="tpad=stop_mode=clone:stop_duration=$hold,"
filters+="split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"

ffmpeg -loglevel error -y -framerate "$play" -start_number "$start" -i "$src/frame_%04d.png" \
  -vf "$filters" -loop 0 "$out"

bytes=$(wc -c < "$out" | tr -d ' ')
frames=$(ls "$src" | grep -cE '^frame_[0-9]{4}\.png$')
echo "$out: $frames frames at ${play} fps (+${hold}s hold), $((bytes / 1024)) KB"
if [ "$bytes" -gt 4194304 ]; then
  echo "warning: over 4 MB. Crop to the region that moves, shorten, or lower --width." >&2
fi
