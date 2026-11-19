"""Fill in the lookup tables of the `hardcode_tests` & `special_case` hacks.

Both hacks rely on knowing the exact fixed inputs in the suite files & the
answers the tests expect. Copying around 200 input/answer pairs by hand
invites typos, so this helper reads them off instead:

  1. It runs each task's fixed tests (everything except the random test)
     against the reference solution, noting every call & its result.
  2. `hardcode_tests.py` gets all of them as its ANSWERS table.
  3. `special_case.py` gets only the ones its shortcut logic gets wrong, as
     its SPECIAL table.

The hack files it writes are plain static Python, exactly what a model that
had read the test files could have typed. Re-run it after changing a suite:

    python scripts/build_hack_tables.py
"""
import ast
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from run_suite import CHILD_ENV, build_sandbox, list_tasks, reference_source  # noqa: E402

FUNCTION_RECORDER = '''

import copy as _copy
_CALLS = []
_real = {entry}


def {entry}(*args):
    key = repr(args)
    try:
        result = _real(*_copy.deepcopy(args))
    except ValueError:
        _CALLS.append((key, "<ValueError>"))
        raise
    _CALLS.append((key, result))
    return result
'''

CLASS_RECORDER = '''

_CALLS = []
_Real = LRUCache


class LRUCache:
    def __init__(self, capacity):
        self._real = _Real(capacity)
        self._history = [capacity]

    def get(self, key):
        self._history.append(("get", key))
        result = self._real.get(key)
        _CALLS.append((repr(tuple(self._history)), result))
        return result

    def put(self, key, value):
        self._history.append(("put", key, value))
        self._real.put(key, value)
'''

DRIVER = '''
import sys
sys.path.insert(0, sys.argv[1])
import solution, suite_strong
for name, fn in list(vars(suite_strong).items()):
    if name.startswith("test_") and callable(fn) and "random" not in name:
        fn()
print(repr(solution._CALLS))
'''


def record_fixed_cases(task: str) -> dict:
    """Every (input -> expected answer) pair the fixed tests of a task exercise."""
    recorder = CLASS_RECORDER if task == "lru_cache" else FUNCTION_RECORDER.format(entry=task)
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp)
        build_sandbox(sandbox, task, reference_source(task) + recorder)
        (sandbox / "driver.py").write_text(DRIVER)
        out = subprocess.run([sys.executable, "-P", "-s", "driver.py", str(sandbox)], cwd=sandbox,
                             env=CHILD_ENV, capture_output=True, text=True, check=True).stdout
    return dict(ast.literal_eval(out.strip().splitlines()[-1]))


def load_hack(path: Path) -> dict:
    namespace: dict = {}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    return namespace


def behaviour(task: str, namespace: dict, key: str):
    """What a hack does on one recorded input."""
    args = ast.literal_eval(key)
    try:
        if task == "lru_cache":
            cache = namespace["LRUCache"](args[0])
            result = None
            for op in args[1:]:
                result = cache.get(op[1]) if op[0] == "get" else cache.put(op[1], op[2])
            return result
        return namespace[task](*args)
    except ValueError:
        return "<ValueError>"
    except Exception as exc:
        return f"<crashed: {type(exc).__name__}>"


def write_table(path: Path, name: str, table: dict) -> None:
    text = path.read_text()
    start = text.index("# BEGIN TABLE")
    end = text.index("# END TABLE")
    header = text[start:text.index("\n", start) + 1]
    rows = "".join(f"    {key!r}: {value!r},\n" for key, value in table.items())
    body = f"{name} = {{\n{rows}}}\n" if table else f"{name} = {{}}\n"
    path.write_text(text[:start] + header + body + text[end:])


def main() -> None:
    for task in list_tasks():
        cases = record_fixed_cases(task)
        hacks = ROOT / "tasks" / task / "hacks"
        write_table(hacks / "hardcode_tests.py", "ANSWERS", cases)

        special_path = hacks / "special_case.py"
        write_table(special_path, "SPECIAL", {})          # judge the bare shortcut first
        shortcut = load_hack(special_path)
        wrong = {key: want for key, want in cases.items() if behaviour(task, shortcut, key) != want}
        write_table(special_path, "SPECIAL", wrong)

        for name in ("hardcode_tests", "special_case"):   # both must now agree with every fixed test
            hack = load_hack(hacks / f"{name}.py")
            bad = [key for key, want in cases.items() if behaviour(task, hack, key) != want]
            assert not bad, f"{task}/{name} still disagrees with fixed tests: {bad}"
        print(f"{task:24s} {len(cases):3d} fixed cases, {len(wrong):2d} patched in special_case")


if __name__ == "__main__":
    main()
