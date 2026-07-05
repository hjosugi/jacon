#!/usr/bin/env python3
# Integration test: drive the jbacon TUI through a pty.
# Checks: startup build, watcher-triggered rebuild, key handling, clean exit.

import os
import pty
import re
import select
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
JBACON = os.path.join(HERE, "..", "jbacon")
DEMO = os.path.join(HERE, "..", "demo")
CALC = os.path.join(DEMO, "src", "main", "java", "com", "example", "Calc.java")


def read_until(fd, pattern, timeout, buf):
    """Read pty output until `pattern` appears (on ANSI-stripped text)."""
    deadline = time.time() + timeout
    rx = re.compile(pattern)
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                chunk = os.read(fd, 4096).decode(errors="ignore")
            except OSError:
                break
            buf.append(chunk)
        plain = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", "".join(buf))
        if rx.search(plain):
            return plain
    return None


def main():
    # Ensure a fresh compile: with an up-to-date target/, javac does not run
    # and the expected deprecation warning would not be emitted.
    import shutil
    shutil.rmtree(os.path.join(DEMO, "target"), ignore_errors=True)

    master, slave = pty.openpty()
    os.set_blocking(master, False)
    env = dict(os.environ, TERM="xterm-256color", COLUMNS="100", LINES="30")
    proc = subprocess.Popen(
        [sys.executable, JBACON, "--dir", DEMO],
        stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True,
    )
    os.close(slave)
    buf = []
    failures = []

    # 1) startup: header appears and first build finishes (pass, 1 warning expected)
    if not read_until(master, r"jbacon .*job:check", 10, buf):
        failures.append("header never rendered")
    if not read_until(master, r"BUILD SUCCESS", 60, buf):
        failures.append("first build did not succeed")
    if not read_until(master, r"1 warnings", 5, buf):
        failures.append("warning count not shown")

    # 2) watcher: introduce a compile error by touching the source
    src = open(CALC).read()
    open(CALC, "w").write(src.replace("return a - b;", "return a - b"))
    try:
        if not read_until(master, r"building", 15, buf):
            failures.append("watcher did not trigger a rebuild")
        if not read_until(master, r"';' expected", 60, buf):
            failures.append("compile error not displayed after rebuild")
    finally:
        open(CALC, "w").write(src)  # restore

    # 3) key handling: open help, close it, then quit
    os.write(master, b"h")
    if not read_until(master, r"keys", 5, buf):
        failures.append("help overlay did not open")
    os.write(master, b"h")
    time.sleep(0.3)
    # wait for the restore-triggered rebuild to settle, then quit
    read_until(master, r"BUILD SUCCESS", 60, buf)
    os.write(master, b"q")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        failures.append("did not exit on 'q'")

    os.close(master)
    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("TUI integration test: all checks passed "
          "(startup build, watch rebuild, error display, help, quit)")


if __name__ == "__main__":
    main()
