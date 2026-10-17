#!/usr/bin/env bash
# Fails (exit 1) if any secret value from .env (KEY/TOKEN/SECRET/PASSWORD names) appears in the staged diff.
# Usage: bash scripts/check_secrets.sh && git commit ...
set -euo pipefail
[ -f .env ] || { echo "no .env; nothing to check"; exit 0; }
hits=0
while IFS='=' read -r name value; do
  [[ -z "${name}" || "${name}" == \#* || -z "${value:-}" ]] && continue
  # only real secrets (names like *KEY*, *TOKEN*, *SECRET*, *PASSWORD*); config such as DATA_REPO may be public
  [[ "${name^^}" =~ (KEY|TOKEN|SECRET|PASSWORD) ]] || continue
  if git diff --cached | grep -qF -- "$value"; then
    echo "SECRET LEAK: value of $name is staged"; hits=$((hits+1))
  fi
done < .env
[ "$hits" -eq 0 ] && echo "secret check: OK (0 leaks)" || exit 1
