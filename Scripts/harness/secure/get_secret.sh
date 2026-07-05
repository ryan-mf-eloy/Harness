#!/usr/bin/env bash
# Retrieve a secret from the macOS Keychain by label. Never call this in a
# way that echoes its output back into a transcript an agent's model reads —
# use it only to feed another subprocess's environment or arguments.
#
# Usage: get_secret.sh <label>
set -euo pipefail

label="${1:?usage: get_secret.sh <label>}"

if ! value="$(security find-generic-password -a "$USER" -s "$label" -w 2>/dev/null)"; then
  echo "ERROR: secret label '$label' not found in Keychain." >&2
  echo "Store it first with:" >&2
  echo "  security add-generic-password -a \"\$USER\" -s \"$label\" -w" >&2
  exit 1
fi

printf '%s' "$value"
