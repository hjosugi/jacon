#!/bin/sh
# Install the latest native jbacon release into ~/.local/bin by default.

set -eu

repo="${JBACON_REPO:-hjosugi/jacon}"
install_dir="${JBACON_INSTALL_DIR:-$HOME/.local/bin}"
version="${JBACON_VERSION:-latest}"

need() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "error: $1 is required" >&2
        exit 2
    fi
}

download() {
    url="$1"
    out="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$out"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$out" "$url"
    else
        echo "error: curl or wget is required" >&2
        exit 2
    fi
}

detect_target() {
    case "$(uname -s)" in
        Linux) os="linux" ;;
        Darwin) os="macos" ;;
        *)
            echo "error: unsupported OS: $(uname -s)" >&2
            exit 2
            ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64) arch="x86_64" ;;
        aarch64) arch="aarch64" ;;
        arm64)
            if [ "$os" = "macos" ]; then
                arch="arm64"
            else
                arch="aarch64"
            fi
            ;;
        *)
            echo "error: unsupported architecture: $(uname -m)" >&2
            exit 2
            ;;
    esac

    printf '%s-%s\n' "$os" "$arch"
}

need tar
need mktemp

target="$(detect_target)"

if [ "$version" = "latest" ]; then
    tmp_json="$(mktemp)"
    download "https://api.github.com/repos/$repo/releases/latest" "$tmp_json"
    version="$(sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$tmp_json" | head -n 1)"
    rm -f "$tmp_json"
    if [ -z "$version" ]; then
        echo "error: could not resolve latest release for $repo" >&2
        exit 1
    fi
fi

case "$version" in
    v*) ;;
    *) version="v$version" ;;
esac

asset="jbacon-$version-$target.tar.gz"
url="https://github.com/$repo/releases/download/$version/$asset"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT INT HUP TERM

archive="$tmp_dir/$asset"
download "$url" "$archive"
tar -xzf "$archive" -C "$tmp_dir"

mkdir -p "$install_dir"
if command -v install >/dev/null 2>&1; then
    install -m 755 "$tmp_dir/jbacon-$version-$target/jbacon" "$install_dir/jbacon"
else
    cp "$tmp_dir/jbacon-$version-$target/jbacon" "$install_dir/jbacon"
    chmod 755 "$install_dir/jbacon"
fi

echo "installed: $install_dir/jbacon"
if ! command -v jbacon >/dev/null 2>&1; then
    echo "note: $install_dir is not in PATH"
fi
"$install_dir/jbacon" --version
