#!/bin/sh
# Build a single-file native jbacon archive for the current platform.

set -eu

root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$root"

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "error: pyinstaller is required (try: python -m pip install pyinstaller)" >&2
    exit 2
fi

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

version="${JBACON_VERSION:-}"
if [ -z "$version" ]; then
    version="$(./jbacon --version | awk '{print $2}')"
fi
case "$version" in
    v*) ;;
    *) version="v$version" ;;
esac

target="${JBACON_TARGET:-$(detect_target)}"
package_dir="dist/package/jbacon-$version-$target"
archive="dist/jbacon-$version-$target.tar.gz"

rm -rf build/pyinstaller dist/jbacon "$package_dir" "$archive"
mkdir -p build/pyinstaller dist/package

pyinstaller \
    --noconfirm \
    --clean \
    --onefile \
    --name jbacon \
    --distpath dist \
    --workpath build/pyinstaller \
    --specpath build/pyinstaller \
    ./jbacon

./dist/jbacon --version

mkdir -p "$package_dir"
cp dist/jbacon README.md LICENSE "$package_dir/"
tar -C dist/package -czf "$archive" "jbacon-$version-$target"

echo "built: $archive"
