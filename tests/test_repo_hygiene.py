"""Checks that the repo's safety settings stay in place."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_gitignore_covers_secrets_and_generated_data():
    lines = (ROOT / ".gitignore").read_text().splitlines()
    for needed in [".env", ".venv/", "__pycache__/", ".pytest_cache/", "*.zip", "data/", "outputs/"]:
        assert needed in lines, f"{needed} missing from .gitignore"


def test_no_tracked_file_over_50mb():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return  # not a git checkout (e.g. a source tarball)
    for name in out.splitlines():
        path = ROOT / name
        if path.is_file():
            assert path.stat().st_size < 50 * 1024 * 1024, f"{name} is over 50 MB"


def test_gitleaks_config_only_allowlists_fake_marker():
    text = (ROOT / ".gitleaks.toml").read_text()
    assert "FAKE" in text
    assert text.count("regexes") == 1
