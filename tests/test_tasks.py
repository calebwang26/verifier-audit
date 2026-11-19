"""Every task must be complete & its reference solution must pass every suite."""
import pytest

from run_suite import SUITES, TASKS_DIR, list_tasks, reference_source, run_many

TASKS = list_tasks()


def test_there_are_twelve_tasks():
    assert len(TASKS) == 12, TASKS


@pytest.mark.parametrize("task", TASKS)
def test_task_has_all_its_files(task):
    for name in ["solution.py", "spec.py", "suite_weak.py", "suite_medium.py", "suite_strong.py"]:
        assert (TASKS_DIR / task / name).is_file(), f"{task}/{name} is missing"


@pytest.mark.parametrize("task", TASKS)
def test_stronger_suites_include_the_weaker_ones(task):
    medium = (TASKS_DIR / task / "suite_medium.py").read_text()
    strong = (TASKS_DIR / task / "suite_strong.py").read_text()
    assert "from suite_weak import *" in medium
    assert "from suite_medium import *" in strong
    assert "oracle" in strong, "the strong suite should include a random check against the oracle"


def test_reference_solutions_pass_every_suite():
    # Passing the oracle suite also shows that each reference agrees with its
    # independently written brute-force oracle on 500 random inputs.
    jobs = [(task, reference_source(task), suite) for task in TASKS for suite in SUITES]
    results = run_many(jobs)
    failures = [(job[0], job[2], res.reason, res.detail) for job, res in zip(jobs, results) if not res.passed]
    assert not failures, failures
