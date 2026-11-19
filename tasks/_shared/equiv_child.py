"""Compares a mutant with the reference on many inputs. Started by equivalence.py.

usage: python equiv_child.py <sandbox_dir> <n_random_inputs> <seed>

The sandbox holds reference.py (the correct solution), solution.py (the
mutant) & spec.py. Prints one result line: either "equivalent on every
input tried" or the first input where the two behave differently.
"""
import copy
import io
import json
import random
import signal
import sys

MARKER = "__EQUIV_RESULT__"
PER_INPUT_SECONDS = 1.0  # the reference needs microseconds; a mutant stuck in a loop gets cut off


class _TimeUp(BaseException):
    """Raised by the alarm. Not an Exception, so candidate code can't swallow it by accident."""


def _on_alarm(signum, frame):
    raise _TimeUp()


def main():
    sandbox_dir, n_inputs, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    sys.path.insert(0, sandbox_dir)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    import reference
    import solution
    import spec
    from checks import outcome

    signal.signal(signal.SIGALRM, _on_alarm)

    def behaviour(module, args):
        signal.setitimer(signal.ITIMER_REAL, PER_INPUT_SECONDS)
        try:
            return outcome(spec.apply, module, copy.deepcopy(args))
        except _TimeUp:
            return ("did not finish", f"{PER_INPUT_SECONDS}s")
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    rng = random.Random(seed)
    inputs = list(spec.EDGE_INPUTS) + [spec.gen_input(rng) for _ in range(n_inputs)]
    result = {"equivalent": True, "inputs_tried": len(inputs)}
    for args in inputs:
        want = behaviour(reference, args)
        got = behaviour(solution, args)
        if got != want:
            result = {"equivalent": False, "input": repr(args)[:200],
                      "reference": repr(want)[:200], "mutant": repr(got)[:200]}
            break
    sys.stdout = real_stdout
    print(MARKER + json.dumps(result))


if __name__ == "__main__":
    main()
