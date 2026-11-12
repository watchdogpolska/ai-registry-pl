#!/usr/bin/env bash
# Release tagging with a monotonic SemVer guard (git + coreutils only).
#
#   scripts/release.sh release patch|minor|major   create the next tag
#   scripts/release.sh release X.Y.Z               create an explicit tag
#   scripts/release.sh check vX.Y.Z                validate a pushed tag (CI)
#
# Tags are vMAJOR.MINOR.PATCH (no pre-release suffixes). A new tag must be
# strictly higher than every existing release tag.
set -euo pipefail

SEMVER_RE='^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'
REMOTE=${REMOTE:-origin}
MAIN_BRANCH=${MAIN_BRANCH:-main}

die() {
    echo "release: $*" >&2
    exit 1
}

# Highest release tag, optionally ignoring one tag (the one being checked).
highest_tag() {
    local exclude=${1:-}
    git tag -l 'v*' | { grep -E "$SEMVER_RE" || true; } |
        { grep -vxF -- "${exclude:-//}" || true; } | sort -V | tail -n 1
}

# True when $1 is strictly higher than $2.
is_higher() {
    [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n 1)" = "$1" ]
}

next_version() {
    local current=$1 bump=$2 major minor patch
    IFS=. read -r major minor patch <<<"${current#v}"
    case $bump in
    major) echo "v$((major + 1)).0.0" ;;
    minor) echo "v${major}.$((minor + 1)).0" ;;
    patch) echo "v${major}.${minor}.$((patch + 1))" ;;
    *) die "unknown bump '$bump' (use patch, minor or major)" ;;
    esac
}

cmd_check() {
    local tag=${1:?usage: release.sh check vX.Y.Z}
    [[ $tag =~ $SEMVER_RE ]] || die "tag '$tag' is not vMAJOR.MINOR.PATCH"

    local previous
    previous=$(highest_tag "$tag")
    if [ -n "$previous" ] && ! is_higher "$tag" "$previous"; then
        die "tag $tag is not higher than existing release $previous"
    fi

    if git rev-parse -q --verify "refs/remotes/$REMOTE/$MAIN_BRANCH" >/dev/null &&
        ! git merge-base --is-ancestor "$tag^{commit}" "$REMOTE/$MAIN_BRANCH"; then
        die "tag $tag points to a commit that is not on $MAIN_BRANCH"
    fi

    echo "release: $tag OK (previous: ${previous:-none})"
}

cmd_release() {
    local arg=${1:?usage: release.sh release patch|minor|major|X.Y.Z}

    [ -z "$(git status --porcelain)" ] || die "working tree is not clean"
    [ "$(git branch --show-current)" = "$MAIN_BRANCH" ] ||
        die "releases are tagged on $MAIN_BRANCH only"

    # Compare against what is published, not a possibly stale local tag list.
    git fetch --quiet --tags "$REMOTE" "$MAIN_BRANCH" ||
        die "cannot fetch tags from $REMOTE (is $MAIN_BRANCH pushed?)"
    [ "$(git rev-parse HEAD)" = "$(git rev-parse "$REMOTE/$MAIN_BRANCH")" ] ||
        die "HEAD differs from $REMOTE/$MAIN_BRANCH; pull/push first"

    if git tag --points-at HEAD | grep -qE "$SEMVER_RE"; then
        die "HEAD is already released as $(git tag --points-at HEAD | grep -E "$SEMVER_RE")"
    fi

    local previous tag
    previous=$(highest_tag)
    case $arg in
    patch | minor | major) tag=$(next_version "${previous:-v0.0.0}" "$arg") ;;
    *) tag="v${arg#v}" ;;
    esac

    [[ $tag =~ $SEMVER_RE ]] || die "'$arg' is not a valid MAJOR.MINOR.PATCH version"
    if [ -n "$previous" ] && ! is_higher "$tag" "$previous"; then
        die "$tag is not higher than the latest release $previous"
    fi

    git tag -a "$tag" -m "$tag"
    echo "release: tagged $tag (previous: ${previous:-none})"
    echo "release: publish with: git push $REMOTE $tag"
}

case ${1:-} in
release) shift && cmd_release "$@" ;;
check) shift && cmd_check "$@" ;;
*) die "usage: release.sh release patch|minor|major|X.Y.Z | check vX.Y.Z" ;;
esac
