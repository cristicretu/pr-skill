#!/usr/bin/env bash
# Check a posted PR body: no local media paths left unuploaded, and every image
# or attachment link in it actually loads (fetched with your gh token, since
# attachment links need a signed-in viewer).
#
#   check-body.sh <pr-number> [-R owner/repo]
set -euo pipefail

pr=${1:?pr number}; shift
body=$(gh pr view "$pr" "$@" --json body --jq .body)
status=0

local_refs=$(grep -oE '(\]\(|src=")\./[^)"]+' <<< "$body" || true)
if [ -n "$local_refs" ]; then
  echo "error: local paths were not uploaded (use ![alt](./file) and pass each file with --attach):" >&2
  sed -E 's/^(\]\(|src=")/  /' <<< "$local_refs" >&2
  status=1
fi

urls=$(grep -oE 'https://(github\.com/user-attachments/(assets|files)/[^)" ]+|raw\.githubusercontent\.com/[^)" ]+|github\.com/[^/]+/[^/]+/blob/[^)" ]+\?raw=true)' <<< "$body" | sort -u || true)
token=$(gh auth token)
n=0
while IFS= read -r url; do
  [ -z "$url" ] && continue
  n=$((n + 1))
  code=$(curl -sL -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $token" "$url")
  if [ "$code" != 200 ]; then
    echo "error: HTTP $code for $url" >&2
    status=1
  fi
done <<< "$urls"

[ "$status" = 0 ] && echo "ok: $n media links load, no local paths left"
exit $status
