"""Draw the 30 mutants for the hand check.

Picks 30 mutants at random (fixed seed) from all mutants of all tasks &
prints each one's change with no audit label next to it, so it can be
judged from the code alone.

    python review/sample.py            # print the 30 changes
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mutate import diff, generate_mutants  # noqa: E402
from run_suite import list_tasks, reference_source  # noqa: E402

SEED = 2026
SAMPLE_SIZE = 30


def draw_sample():
    """[(task, Mutant)] for the 30 sampled mutants, in a fixed order."""
    everything = [(task, m) for task in list_tasks() for m in generate_mutants(reference_source(task))]
    chosen = random.Random(SEED).sample(range(len(everything)), SAMPLE_SIZE)
    return [everything[i] for i in sorted(chosen)]


if __name__ == "__main__":
    for task, m in draw_sample():
        print(f"\n### {task} {m.id}  [{m.operator}]")
        print(diff(reference_source(task), m))
