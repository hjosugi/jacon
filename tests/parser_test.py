#!/usr/bin/env python3
# Unit tests for the maven output parser in jbacon.

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_loader("jbacon", loader=None)
mod = importlib.util.module_from_spec(spec)
src = open(os.path.join(HERE, "..", "jbacon")).read()
# Do not run main() when loading the script as a module.
exec(compile(src.replace('if __name__ == "__main__":', 'if False:'), "jbacon", "exec"),
     mod.__dict__)

FIXTURE = """\
[INFO] Scanning for projects...
[WARNING] Using platform encoding (UTF-8) to copy filtered resources
[INFO] --- maven-compiler-plugin:3.13.0:compile (default-compile) @ demo ---
[WARNING] /work/src/main/java/com/example/Calc.java:[14,21] Integer(int) has been deprecated
[ERROR] /work/src/main/java/com/example/Calc.java:[10,21] ';' expected
[INFO] BUILD FAILURE
[ERROR] Failed to execute goal maven-compiler-plugin:3.13.0:compile on project demo: Compilation failure -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException
[ERROR] /work/src/main/java/com/example/Calc.java:[10,21] ';' expected
"""

SUREFIRE = """\
[ERROR] com.example.CalcTest.subFails -- Time elapsed: 0.05 s <<< FAILURE!
[ERROR]   CalcTest.subFails:14 expected: <99> but was: <3>
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0
[INFO] BUILD FAILURE
"""


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def main():
    r = mod.parse_output(FIXTURE.splitlines(keepends=True), "/work")

    check(r.status == "FAILURE", "status should be FAILURE")
    errs, warns = r.errors, r.warnings
    check(len(errs) == 2, f"expected 2 errors (1 located, 1 goal), got {len(errs)}: "
          + "; ".join(e.msg for e in errs))
    check(len(warns) == 2, f"expected 2 warnings, got {len(warns)}")
    # errors must come before warnings
    check(r.items[0].sev == "ERROR", "errors must sort before warnings")
    # located error first, relative path, line/col parsed
    e0 = r.items[0]
    check(e0.path == "src/main/java/com/example/Calc.java", f"bad relpath: {e0.path}")
    check((e0.line, e0.col) == (10, 21), "line/col not parsed")
    # dedup: the repeated located error appears once
    located = [e for e in errs if e.path]
    check(len(located) == 1, "duplicate located error was not deduplicated")
    # noise: -> [Help 1] suffix stripped, help/rerun lines dropped
    goal = [e for e in errs if not e.path][0]
    check("[Help" not in goal.msg, "help suffix not stripped")
    check(all("Re-run" not in i.msg for i in r.items), "noise line leaked")

    r2 = mod.parse_output(SUREFIRE.splitlines(keepends=True), "/work")
    check(r2.tests_summary and "Failures: 1" in r2.tests_summary,
          "tests summary not captured")
    check(any("expected: <99>" in i.msg for i in r2.items),
          "assertion message not captured")
    check(r2.status == "FAILURE", "surefire failure status")

    print("parser unit tests: all checks passed")


if __name__ == "__main__":
    main()
