import yaml
from pathlib import Path


def test_workflow_file_exists():
    """Test that the workflow file exists."""
    workflow_file = Path(".github/workflows/release.yml")
    assert workflow_file.exists(), "Release workflow file not found"


def test_workflow_syntax():
    """Test that the workflow file has valid YAML syntax."""
    workflow_file = Path(".github/workflows/release.yml")
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Test basic structure
    assert "name" in workflow
    assert True in workflow  # This is the 'on' key in the YAML
    assert "jobs" in workflow

    # Test trigger configuration
    trigger_config = workflow[True]  # This is the 'on' section
    assert "push" in trigger_config
    assert "tags" in trigger_config["push"]
    assert trigger_config["push"]["tags"] == ["v*"]

    # Test jobs
    required_jobs = {
        "build",
        "test",
        "security-scan",
        "publish-testpypi",
        "publish-pypi",
        "release-notes",
    }
    assert set(workflow["jobs"].keys()) == required_jobs

    # Test build job
    build_job = workflow["jobs"]["build"]
    assert build_job["runs-on"] == "ubuntu-latest"
    assert "steps" in build_job

    # Test test job
    test_job = workflow["jobs"]["test"]
    assert test_job["runs-on"] == "ubuntu-latest"
    # Handle both string and list types for needs
    needs = test_job["needs"]
    assert needs == "build" or needs == ["build"]
    assert "steps" in test_job

    # Test security scan job
    security_job = workflow["jobs"]["security-scan"]
    assert security_job["runs-on"] == "ubuntu-latest"
    needs = security_job["needs"]
    assert needs == "build" or needs == ["build"]
    assert "steps" in security_job

    # Test TestPyPI publish job
    testpypi_job = workflow["jobs"]["publish-testpypi"]
    assert testpypi_job["runs-on"] == "ubuntu-latest"
    needs = testpypi_job["needs"]
    assert isinstance(needs, list)
    assert set(needs) == {"build", "test", "security-scan"}
    assert "steps" in testpypi_job

    # Test PyPI publish job
    pypi_job = workflow["jobs"]["publish-pypi"]
    assert pypi_job["runs-on"] == "ubuntu-latest"
    needs = pypi_job["needs"]
    assert needs == "publish-testpypi" or needs == ["publish-testpypi"]
    assert pypi_job["environment"] == "pypi-production"
    assert "steps" in pypi_job

    # Test release notes job
    release_job = workflow["jobs"]["release-notes"]
    assert release_job["runs-on"] == "ubuntu-latest"
    needs = release_job["needs"]
    assert needs == "publish-pypi" or needs == ["publish-pypi"]
    assert "permissions" in release_job
    assert release_job["permissions"]["contents"] == "write"
    assert "steps" in release_job


def test_workflow_dependencies():
    """Test that all required dependencies are installed in the workflow."""
    workflow_file = Path(".github/workflows/release.yml")
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)

    # Check build dependencies
    build_steps = workflow["jobs"]["build"]["steps"]
    build_deps = next(
        (step for step in build_steps if step["name"] == "Install build dependencies"),
        None,
    )
    assert build_deps is not None
    assert "pip install build" in build_deps["run"]

    # Check test dependencies
    test_steps = workflow["jobs"]["test"]["steps"]
    test_deps = next(
        (step for step in test_steps if step["name"] == "Install test dependencies"),
        None,
    )
    assert test_deps is not None
    assert "pip install pytest" in test_deps["run"]

    # Check security tool dependencies
    security_steps = workflow["jobs"]["security-scan"]["steps"]
    security_deps = next(
        (step for step in security_steps if step["name"] == "Install security tools"),
        None,
    )
    assert security_deps is not None
    assert "pip install pip-audit bandit" in security_deps["run"]
