#!/usr/bin/env fish
# Install jbacon to ~/.local/bin (fish shell).
# Usage: fish install.fish

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
