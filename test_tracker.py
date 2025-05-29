import os
import subprocess
from pathlib import Path

# Path to the tracker script under test
script_path = Path(__file__).parent / "tasker.py"
assert script_path.exists(), "❌ tasker.py not found alongside tests."

USE_PLAIN = True  # run tracker in --plain mode so output is ASCII‑safe

def warn_if_non_utf8():
    """Warn Windows users if the console isn't set to UTF-8 (codepage 65001)."""
    if os.name == "nt":
        try:
            cp = subprocess.run("chcp", shell=True, capture_output=True, text=True, check=False)
            if "65001" not in cp.stdout:
                print("⚠️  Console code-page is not UTF-8. Run `chcp 65001` for emoji support.")
        except Exception as exc:
            print("(warning) couldn't determine code-page:", exc)


def run(cmd: str, stdin_data=None):
    """Run a shell command, inject --plain, capture output, and echo for debugging."""
    if USE_PLAIN:
        parts = cmd.split()
        # python <script>  --> insert --plain just after script path (index 2)
        if len(parts) > 2 and parts[0].lower() == "python":
            parts.insert(2, "--plain")
        cmd = " ".join(parts)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True, env=env,
        input=stdin_data,
        check=False)
    print("COMMAND:", cmd)
    print("EXIT:", res.returncode)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    return res


def fresh_store() -> str:
    """Return path to a fresh JSON store file, deleting any previous copy."""
    p = Path("test_storage.json")
    p.unlink(missing_ok=True)
    return str(p)

# -------- individual tests -------- #

def test_add():
    store = fresh_store()
    out = run(f"python {script_path} --store {store} add Write_test_scaffolding")
    assert "Added" in out.stdout


def test_status():
    store = fresh_store()
    run(f"python {script_path} --store {store} add Check_status_rendering")
    out = run(f"python {script_path} --store {store} status")
    assert "Check status rendering".replace(" ", "_") in out.stdout


def test_backlog():
    store = fresh_store()
    run(f"python {script_path} --store {store} backlog add Refactor_storage_loader")
    lst = run(f"python {script_path} --store {store} backlog list")
    assert "Refactor storage loader".replace(" ", "_") in lst.stdout
    run(f"python {script_path} --store {store} done")  # clear active if any
    pulled = run(f"python {script_path} --store {store} backlog pull")
    assert "Pulled from backlog" in pulled.stdout

def test_done_prompt_pull():
    """
    Flow:
      1. Add backlog item
      2. Add active task
      3. Run `done` and feed 'p\\n' to pull from backlog
      4. Verify the backlog item became the new active task
    """
    store = fresh_store()

    # Step 1: add backlog item
    run(f"python {script_path} --store {store} backlog add 'Pulled task'")

    # Step 2: add active task
    run(f"python {script_path} --store {store} add 'Original active'")

    # Step 3: complete active task and choose 'p' to pull next
    result = run(
        f"python {script_path} --store {store} done",
        stdin_data="p\n"      # feed choice "p"
    )
    assert "Pulled from backlog" in result.stdout

    # Step 4: status should now show the pulled task as active
    status = run(f"python {script_path} --store {store} status")
    assert "Pulled task" in status.stdout


def main():
    warn_if_non_utf8()
    test_add()
    test_status()
    test_backlog()
    test_done_prompt_pull()
    print("✅ ALL TESTS PASSED")

if __name__ == "__main__":
    main()
