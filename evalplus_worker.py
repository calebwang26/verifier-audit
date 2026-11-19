"""Evaluates many candidate programs for ONE HumanEval problem. Started by evalplus_check.py.

usage: python evalplus_worker.py <job.json>      (prints one JSON result line)

The job holds the problem's reference solution, its original HumanEval test
inputs ("base"), its extra HumanEval+ inputs ("plus") & a list of candidate
programs (mutants & model-written samples). For each candidate the answer
is one letter:

    B   fails a base input                      (wrong, & the original tests notice)
    P   passes every base input, fails a plus   (wrong, & the original tests DON'T notice)
    O   passes everything

The candidates are untrusted model-written code, so each runs in its own
forked child process with:
  * a time limit per input & a hard limit overall,
  * destructive functions (os.remove, os.system, subprocess, ...) switched off,
  * its output thrown away.
The comparison rules copy EvalPlus's own (exact match, a small tolerance for
floats, & "any root is fine" for find_zero). The switched-off list follows
the `reliability_guard` used by HumanEval & EvalPlus.
"""
import copy
import io
import json
import os
import select
import signal
import sys
import time

MIN_INPUT_SECONDS = 1.0     # each input gets at least this long...
REF_TIME_FACTOR = 4.0       # ...or this many times what the reference needed
HARD_LIMIT_SECONDS = 60.0   # per candidate, everything included
FLOAT_RTOL = 1e-07


class _TimeUp(BaseException):
    """Not an Exception, so a candidate's own `except Exception` can't swallow it."""


def _on_alarm(signum, frame):
    raise _TimeUp()


class time_limit:
    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        signal.setitimer(signal.ITIMER_REAL, self.seconds)

    def __exit__(self, *exc):
        signal.setitimer(signal.ITIMER_REAL, 0)
        return False


def is_floats(value):
    if isinstance(value, float):
        return True
    if isinstance(value, (list, tuple)) and value:
        return all(isinstance(item, float) for item in value)
    return False


def _close(a, b, atol):
    if a == b:
        return True
    return abs(a - b) <= atol + FLOAT_RTOL * abs(b)


def allclose(out, exp, atol):
    try:
        if isinstance(exp, (list, tuple)):
            return all(_close(a, b, atol) for a, b in zip(out, exp))
        return _close(out, exp, atol)
    except Exception:
        return False


def poly(xs, x):
    return sum(coeff * x ** power for power, coeff in enumerate(xs))


def same(entry_point, atol, inp, out, exp):
    """EvalPlus's rule for "the candidate's output matches the expected output"."""
    if entry_point == "find_zero":            # any root of the polynomial is correct
        return abs(poly(inp[0], out)) <= atol
    exact = bool(out == exp)
    if atol == 0 and is_floats(exp):
        atol = 1e-6
    if not exact and atol != 0:
        if type(out) is not type(exp):
            return False
        if isinstance(exp, (list, tuple)) and len(out) != len(exp):
            return False
        return allclose(out, exp, atol)
    return exact


def reliability_guard():
    """Switch off things a stray program could use to damage the machine."""
    import builtins
    import faulthandler
    import shutil
    import subprocess

    faulthandler.disable()
    builtins.exit = None
    builtins.quit = None
    builtins.help = None
    for name in ["kill", "system", "putenv", "remove", "removedirs", "rmdir", "fchdir", "setuid",
                 "fork", "forkpty", "killpg", "rename", "renames", "truncate", "replace", "unlink",
                 "fchmod", "fchown", "chmod", "chown", "chroot", "lchflags", "lchmod", "lchown",
                 "getcwd", "chdir", "execv", "execve", "popen", "posix_spawn"]:
        if hasattr(os, name):
            setattr(os, name, None)
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None
    subprocess.Popen = None
    for module in ["ipdb", "joblib", "resource", "psutil", "tkinter"]:
        sys.modules[module] = None


def run_reference(job):
    """Expected outputs & time limits, from the trusted reference solution."""
    env = {}
    exec(job["reference"], env)
    fn = env[job["entry_point"]]
    expected, limits = {}, {}
    for stage in ("base", "plus"):
        expected[stage], limits[stage] = [], []
        for inp in job[f"{stage}_input"]:
            started = time.perf_counter()
            expected[stage].append(fn(*copy.deepcopy(inp)))
            took = time.perf_counter() - started
            limits[stage].append(max(MIN_INPUT_SECONDS, REF_TIME_FACTOR * took))
    return expected, limits


def child_evaluate(job, code, expected, limits, report):
    """Runs inside the forked child. Calls report(b"1") once the base inputs all pass."""
    reliability_guard()
    env = {}
    try:
        with time_limit(10.0):
            exec(code, env)
        fn = env[job["entry_point"]]
    except BaseException:
        return b"B"
    for stage, fail_letter in (("base", b"B"), ("plus", b"P")):
        for inp, exp, limit in zip(job[f"{stage}_input"], expected[stage], limits[stage]):
            try:
                with time_limit(limit):
                    out = fn(*copy.deepcopy(inp))
                ok = same(job["entry_point"], job["atol"], inp, out, exp)
            except BaseException:
                ok = False
            if not ok:
                return fail_letter
        if stage == "base":
            report(b"1")
    return b"O"


def evaluate_candidate(job, code, expected, limits):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:  # ---- child ----
        os_write, os_exit = os.write, os._exit
        try:
            os.close(read_fd)
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            signal.signal(signal.SIGALRM, _on_alarm)
            letter = child_evaluate(job, code, expected, limits, lambda mark: os_write(write_fd, mark))
            os_write(write_fd, letter)
        except BaseException:
            pass
        finally:
            os_exit(0)
    # ---- parent ----
    os.close(write_fd)
    received = b""
    deadline = time.time() + HARD_LIMIT_SECONDS
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        ready, _, _ = select.select([read_fd], [], [], remaining)
        if not ready:
            break
        chunk = os.read(read_fd, 64)
        if not chunk:
            break  # child closed the pipe: it's done (or died)
        received += chunk
    os.close(read_fd)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    os.waitpid(pid, 0)
    if b"O" in received:
        return "O"
    # No verdict means the child was killed or died. If it had already
    # reported passing the base inputs, it failed somewhere in the plus inputs.
    if b"P" in received or b"1" in received:
        return "P"
    return "B"


def main():
    job = json.load(open(sys.argv[1]))
    expected, limits = run_reference(job)
    statuses = [evaluate_candidate(job, code, expected, limits) for code in job["candidates"]]
    print("__WORKER_RESULT__" + json.dumps({"statuses": statuses}))


if __name__ == "__main__":
    main()
