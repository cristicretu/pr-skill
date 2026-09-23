#!/usr/bin/env bash
# Print commit-pinned markdown image lines for every media file in a directory,
# after checking the commit is pushed and actually contains each file.
#
#   media-urls.sh docs/screenshots/<feature> [--check]
#
# Public repos get raw.githubusercontent.com URLs. Private repos get
# github.com/<repo>/blob/<sha>/<path>?raw=true, which renders for anyone who
# can read the repo (raw.githubusercontent.com would 404 for them).
# --check fetches each URL (public repos only) and fails on anything but 200.
#
# Alt text is derived from the file name (dark-to-light.gif -> "dark to light");
# edit it to say what the image shows.
set -euo pipefail

dir=${1:?media directory, relative to the repo root}; check=${2:-}
root=$(git rev-parse --show-toplevel)
cd "$root"
dir=${dir%/}

sha=$(git rev-parse HEAD)
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ -z "$upstream" ]; then
  echo "error: branch has no upstream. git push -u origin <branch> first." >&2; exit 1
fi
git fetch --quiet "${upstream%%/*}" 2>/dev/null || true
if ! git merge-base --is-ancestor "$sha" "$upstream"; then
  echo "error: HEAD $sha is not pushed to $upstream. Push first; unpushed SHAs render as broken images." >&2; exit 1
fi

read -r repo private < <(gh repo view --json nameWithOwner,isPrivate --jq '"\(.nameWithOwner) \(.isPrivate)"')

files=$(git ls-tree -r --name-only "$sha" -- "$dir" | grep -iE '\.(png|jpe?g|gif|webp|svg)$' || true)
if [ -z "$files" ]; then
  echo "error: no committed media under $dir at $sha" >&2; exit 1
fi

status=0
while IFS= read -r path; do
  if [ "$private" = true ]; then
    url="https://github.com/$repo/blob/$sha/$path?raw=true"
  else
    url="https://raw.githubusercontent.com/$repo/$sha/$path"
  fi
  name=$(basename "$path"); alt=${name%.*}; alt=${alt//[-_]/ }
  echo "![$alt]($url)"
  if [ "$check" = "--check" ] && [ "$private" != true ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' "$url")
    [ "$code" = 200 ] || { echo "  ^ HTTP $code" >&2; status=1; }
  fi
done <<< "$files"
exit $status
