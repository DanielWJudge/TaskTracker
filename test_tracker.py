import os
import sys
import json
import subprocess
from pathlib import Path

script_path = Path(__file__).parent / "tasker.py"
assert script_path.exists(), "❌ tasker.py not found in the same directory."

def check_windows_codepage():
    if os.name == "nt":
        try:
            cp_result = subprocess.run("chcp", shell=True, capture_output=True, text=True)
            if "65001" not in cp_result.stdout:
                print("⚠️ Your terminal is not using UTF-8. Run `chcp 65001` before running this script to fix emoji output.")
        except Exception as e:
            print("(Warning) Failed to check codepage:", e)

def run(command):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    print("COMMAND:", command)
    print("RETURN CODE:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    return result

def setup_test_storage():
    test_file = Path("test_storage.json")
    if test_file.exists():
        test_file.unlink()
    return str(test_file)

def test_add_task():
    store = setup_test_storage()
    result = run(f"python {script_path} --store {store} add 'Write test scaffolding'")
    assert "Added" in result.stdout

def test_status_output():
    store = setup_test_storage()
    run(f"python {script_path} --store {store} add 'Check status rendering'")
    result = run(f"python {script_path} --store {store} status")
    assert "Check status rendering" in result.stdout

def test_backlog_add_and_pull():
    store = setup_test_storage()
    run(f"python {script_path} --store {store} backlog add 'Refactor storage loader'")
    result = run(f"python {script_path} --store {store} backlog list")
    assert "Refactor storage loader" in result.stdout
    run(f"python {script_path} --store {store} done")  # Clear active
    result = run(f"python {script_path} --store {store} backlog pull")
    assert "Pulled from backlog" in result.stdout

def run_all_tests():
    check_windows_codepage()
    test_add_task()
    test_status_output()
    test_backlog_add_and_pull()
    print("✅ All tests passed!")

if __name__ == "__main__":
    run_all_tests()
