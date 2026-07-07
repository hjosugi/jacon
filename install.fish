#!/usr/bin/env fish
# Install this checkout's Python script to ~/.local/bin (fish shell).
# For native release binaries, use: curl -fsSL https://raw.githubusercontent.com/hjosugi/jacon/main/install.sh | sh

set -l here (dirname (status filename))
set -l dest ~/.local/bin

mkdir -p $dest
cp $here/jbacon $dest/jbacon
chmod +x $dest/jbacon

if not contains $dest $PATH
    echo "NOTE: $dest is not in PATH. Add it with:"
    echo "  fish_add_path $dest"
end

echo "installed: $dest/jbacon"
echo "run inside any Maven project:  jbacon"
