<!-- i18n: language-switcher -->
[English](README.en.md) | [日本語](README.md)

# jbacon

A bacon-style background code checker for Maven projects.
When running alongside your editor (in a terminal or VSCode integrated terminal), it automatically runs build checks every time you save a file, displaying sorted errors and warnings in real-time.

```
 jbacon 0.2.0  job:check  mvn  fail  2 errors, 0 warnings
E src/main/java/com/example/Calc.java:9:21
   ';' expected
E Failed to execute goal
  org.apache.maven.plugins:maven-compiler-plugin:3.13.0:compile (default-compile) on
  project jbacon-demo: Compilation failure

 BUILD FAILURE in 3.5s
 c:check  t:test  v:verify  p:package  r:rerun o:offline s:summary w:raw h:help q:quit
```

(↑ Actual rendered output. See `tests/screenshot.txt`)

## Features (Design borrowed from bacon)

- **Resident mode with auto rebuild on save**: Watches `src/` and `pom.xml`. Automatically detects multi-module projects up to 3 levels deep.
- **Errors before warnings**: Sorted by location-specific errors → general errors → warnings. The most important info appears at the top, so no scrolling needed.
- **One-key job switching**: `c` compile / `t` test / `v` verify / `p` package. Same feel as bacon’s `t` / `c` / `d`.
- **Retains previous results while recalculating**: The previous error list remains visible during builds.
- **Duplicate removal**: Absorbs Maven’s issue of outputting compile errors twice (main message + summary).
- **Immediate build cancellation**: If you save again during a build, the old build is killed and only the latest runs (equivalent to `watchexec -r`).
- **Lightweight**: Uses only Python standard library, zero dependencies, single file. Monitoring is done by mtime polling (excluding `target/` and `.git/`).
- **Automatic mvnd detection**: Automatically selects `mvnd` > `./mvnw` > `mvn`. If `mvnd` is available, JVM stays resident for speed.
- **`--once` mode**: For CI or pre-commit checks. Runs once without TUI and returns exit code.

## Requirements

- One of `mvn` / `mvnd` / `./mvnw`
- Linux or macOS terminal (Windows via WSL)
- If using native release binary, Python is not required
- If using source directly, Python 3.11+ (uses `tomllib`; works with 3.8+ if no config file is used)

## Installation

```bash
# Easiest: install native standalone binary to ~/.local/bin/jbacon
curl -fsSL https://raw.githubusercontent.com/hjosugi/jacon/main/install.sh | sh

# To install from source checkout: fish shell (e.g. CachyOS)
fish install.fish

# Or manually
cp jbacon ~/.local/bin/ && chmod +x ~/.local/bin/jbacon
```

Native releases are provided for Linux x86_64 / Linux aarch64 / macOS x86_64 / macOS arm64.
To install a specific version, set `JBACON_VERSION=v0.2.0`.
To change install location, set `JBACON_INSTALL_DIR=/path/to/bin`.

For faster builds, `mvnd` is recommended:

```bash
sdk install mvnd          # SDKMAN
# Arch-based: check AUR with paru -Ss mvnd
```

## Usage

```bash
cd your-maven-project
jbacon                    # Start resident mode with default job (check = test-compile)
jbacon --job test         # Start with test monitoring
jbacon --once             # Run once, output report, then exit (for CI)
jbacon --mvn mvnd         # Explicitly specify Maven executable
jbacon --offline          # Run with -o (offline) option
```

### Key bindings

| Key | Action |
|---|---|
| `c` | check job (test-compile) |
| `t` | test job |
| `v` | verify job |
| `p` | package job (-DskipTests) |
| `r` | manual rerun |
| `o` | toggle offline mode (-o) |
| `s` | toggle summary display (one diagnostic per line) |
| `w` | toggle raw Maven log display |
| `h` | help / job list |
| `j` `k` / arrows | scroll |
| `g` `G` | go to top / bottom |
| `q` | quit |

## Configuration (jbacon.toml)

Place a `jbacon.toml` in your project root to add or override jobs.
The bundled `jbacon.toml` includes commented samples. Common examples:

```toml
extra_args = ["-T1C"]        # Additional arguments for all builds

[jobs.focus]                 # Watch only one test class
key = "f"
goals = ["test", "-Dtest=CalcTest"]

[jobs.errorprone]            # Static analysis with Error Prone profile
key = "e"
goals = ["clean", "test-compile", "-Perrorprone"]
```

## VSCode Integration

Copy `vscode/tasks.json` to your project’s `.vscode/tasks.json`.
Run `Ctrl+Shift+P` → Tasks: Run Task → `jbacon: watch` to start resident mode in a dedicated panel.
(`runOn: folderOpen` is enabled, so it starts automatically when opening the folder).

Recommended setup (3 layers):

1. **Real-time in-editor**: Extension Pack for Java + SonarQube for IDE.
   Immediate per-file errors handled here (equivalent to IntelliJ).
2. **jbacon resident**: Ensures the entire module really compiles/tests successfully.
   Catches overall consistency issues that incremental editor analysis misses.
3. **Error Prone / SpotBugs**: Run as jbacon jobs only when needed.

## Design notes on lightness

- The cost per save is only the Maven execution time. jbacon’s own monitoring uses mtime polling (default 0.7s interval, excluding `target/`), so CPU usage is almost zero.
- Using `mvnd` caches JVM, plugin class loaders, and JIT code between builds, making `test-compile` feel much faster.
- The default job is `test-compile` (does not run package or install) for lightness. This is sufficient to check if compilation passes.

## Verification

Try it with the bundled demo project (first run downloads dependencies):

```bash
cd demo
../jbacon
# In another window, remove a semicolon in src/main/java/com/example/Calc.java and save
# → Error immediately appears at the top
```

Tests:

```bash
python3 tests/parser_test.py   # Parser unit tests
python3 tests/tui_test.py      # TUI integration tests via pty (requires mvn + JDK)
```

Parser tests run in CI. TUI integration tests run locally with `mvn` + JDK installed.

## Release

Pushing a tag triggers GitHub Actions to create native release assets with PyInstaller.

```bash
git tag v0.2.0
git push origin main v0.2.0
```

## Limitations

- Diagnostic parsing depends on Maven’s `[ERROR]` / `[WARNING]` format (`-B`, `color=never`).
  Location-aware diagnostics are only supported for `.java` / `.kt` / `.kts` / `.groovy`.
  Gradle is not supported (use Gradle’s built-in `--continuous` instead).
- File watching uses polling, not inotify. For huge monorepos (tens of thousands of files), increase `poll_interval` or narrow scope with `watch`.

## License

0BSD. You can use, copy, modify, and distribute this project for almost any purpose.