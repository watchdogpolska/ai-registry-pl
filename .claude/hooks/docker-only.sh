#!/usr/bin/env bash
# PreToolUse hook: this project is developed only inside Docker containers.
# Blocks Bash commands that run Python/Node tooling directly on the host.
# Anything routed through `make` or `docker`/`docker compose` is allowed.

raw=$(jq -r '.tool_input.command // empty')
[ -z "$raw" ] && exit 0

# Ignore quoted strings (commit messages, grep patterns), but still inspect the
# bodies of `sh -c "..."` / `bash -c '...'`, which are executed.
cmd=$(printf '%s' "$raw" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")
cmd+=$'\n'$(printf '%s' "$raw" | grep -oE -- "-c +(\"[^\"]*\"|'[^']*')" | sed -E "s/^-c +.//; s/.\$//")

# Commands that go through the containers are fine.
if printf '%s' "$cmd" | grep -qE '(^|[;&|(]|\s)(docker|make)(\s|$)'; then
    exit 0
fi

# Host tooling in command position: start of line or after ; & | ( or `env VAR=...`.
tools='python[0-9.]*|pip[0-9.]*|pipx|uv|poetry|yarn|npm|npx|pnpm|node|black|isort|django-admin|sass|postcss|(\./)?manage\.py'
if printf '%s' "$cmd" | grep -qE "(^|[;&|(\`]|\\\$\()\s*([A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(sudo\s+)?(\S*/)?($tools)(\s|$)"; then
    echo "Blocked: this project runs only in Docker. Use a make target (see 'make help') or 'docker compose run --rm django ...' / 'docker compose run --rm scss-compile ...' instead of host python/pip/yarn/npm/node." >&2
    exit 2
fi

exit 0
