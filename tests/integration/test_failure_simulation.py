import os
import subprocess
import pytest


@pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION") != "1",
    reason="Integration tests disabled by default. Set RUN_INTEGRATION=1 to enable.",
)
def test_kill_worker_and_recover(tmp_path):
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "kill_worker_and_recover.sh"))
    # Make sure script is executable
    subprocess.run(["chmod", "+x", script], check=True)

    # Run the integration script; it returns 0 on success
    proc = subprocess.run([script, "2.22", "integration-test"], cwd=os.getcwd())
    assert proc.returncode == 0, f"Integration script failed (exit {proc.returncode})"
