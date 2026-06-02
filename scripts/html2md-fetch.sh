#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: html2md-fetch <url> [args...]" >&2
  exit 2
fi

url=$1
shift

command_template=${HTML2MD_FETCH_COMMAND:-'html2md ${url}'}
printf -v escaped_url "%q" "$url"
command=${command_template//\$\{url\}/$escaped_url}

if [[ $# -gt 0 ]]; then
  exec bash -c "$command \"\$@\"" -- "$@"
fi

exec bash -c "$command"
