"""Runs one test suite inside a sandbox folder. Started by run_suite.py.

usage: python harness.py <sandbox_dir> <suite_module_name>

Imports the suite (which imports the candidate `solution`), calls every
function whose name starts with `test_`, then prints one result line.
Exit code 0 means every test passed.
"""
import importlib
import io
import json
import sys

MARKER = "__SUITE_RESULT__"


def main():
    sandbox_dir, suite_name = sys.argv[1], sys.argv[2]
    sys.path.insert(0, sandbox_dir)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()  # candidates may print; keep our result line clean
    result = {"passed": True, "reason": "pass", "detail": "", "tests_run": 0}
    try:
        suite = importlib.import_module(suite_name)
        tests = [(name, fn) for name, fn in vars(suite).items()
                 if name.startswith("test_") and callable(fn)]
        for name, fn in tests:
            result["detail"] = name
            fn()
            result["tests_run"] += 1
        result["detail"] = ""
    except AssertionError as exc:
        result.update(passed=False, reason="assertion",
                      detail=f"{result['detail']}: {str(exc)[:300]}")
    except BaseException as exc:  # includes SystemExit raised by a candidate
        result.update(passed=False, reason="error",
                      detail=f"{result['detail']}: {type(exc).__name__}: {str(exc)[:300]}")
    sys.stdout = real_stdout
    print(MARKER + json.dumps(result))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
