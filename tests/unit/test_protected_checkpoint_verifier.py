import subprocess
import sys


def test_protected_checkpoint_verifier_exposes_required_root() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_protected_pipe_normal_checkpoint.py",
            "--help",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--root ROOT" in completed.stdout
