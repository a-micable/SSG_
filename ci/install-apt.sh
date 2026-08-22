#!/usr/bin/env bash
set -euo pipefail
LOCK_FILE="${1:-ci/apt-packages.lock}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  pkg="${line%%=*}"
  ver="${line#*=}"
  if apt-get install -y --no-install-recommends "${pkg}=${ver}"; then
    continue
  fi
  echo "Pinned version ${pkg}=${ver} unavailable; installing unpinned ${pkg}" >&2
  apt-get install -y --no-install-recommends "${pkg}"
done < "${LOCK_FILE}"
