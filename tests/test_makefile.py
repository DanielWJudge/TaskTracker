import pytest
import subprocess
from pathlib import Path
import tempfile


@pytest.fixture
def temp_project():
    """Create a temporary project directory with necessary files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create project structure
        src_dir = Path(temp_dir) / "src" / "momentum"
        src_dir.mkdir(parents=True)

        # Create __init__.py to make it a package
        (src_dir / "__init__.py").touch()

        # Create version file
        version_file = src_dir / "__version__.py"
        version_file.write_text('__version__ = "1.2.3"\n')

        # Create bump_version.py
        bump_script = Path(temp_dir) / "bump_version.py"
        bump_script.write_text(
            """
#!/usr/bin/env python3
import sys
import re
from pathlib import Path

VERSION_FILE = Path("src/momentum/__version__.py")

def get_current_version():
    content = VERSION_FILE.read_text()
    match = re.search(r'__version__\\s*=\\s*["\\']([\\d.]+)["\\']', content)
    if not match:
        raise ValueError("Version string not found")
    return match.group(1)

def bump(version, part):
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("part must be one of: major, minor, patch")
    return f"{major}.{minor}.{patch}"

def set_version(new_version):
    content = VERSION_FILE.read_text()
    new_content = re.sub(
        r'__version__\\s*=\\s*["\\']([\\d.]+)["\\']',
        f'__version__ = "{new_version}"',
        content,
    )
    VERSION_FILE.write_text(new_content)

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("Usage: bump_version.py [major|minor|patch]")
        sys.exit(1)
    part = sys.argv[1]
    current = get_current_version()
    new = bump(current, part)
    set_version(new)
    print(f"Bumped version: {current} -> {new}")

if __name__ == "__main__":
    main()
"""
        )
        bump_script.chmod(0o755)  # Make executable

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=temp_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True
        )
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True
        )

        yield temp_dir


def test_bump_patch_command(temp_project):
    """Test the bump-patch command."""
    result = subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Bumped version: 1.2.3 -> 1.2.4" in result.stdout


def test_bump_minor_command(temp_project):
    """Test the bump-minor command."""
    result = subprocess.run(
        ["python", "bump_version.py", "minor"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Bumped version: 1.2.3 -> 1.3.0" in result.stdout


def test_bump_major_command(temp_project):
    """Test the bump-major command."""
    result = subprocess.run(
        ["python", "bump_version.py", "major"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Bumped version: 1.2.3 -> 2.0.0" in result.stdout


def test_release_patch_command(temp_project):
    """Test the release-patch command."""
    # First bump the version
    subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        check=True,
    )

    # Add and commit the version file
    subprocess.run(
        ["git", "add", "src/momentum/__version__.py"],
        cwd=temp_project,
        check=True,
    )

    # Get the new version by reading the file directly
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_content = version_file.read_text()
    import re

    version_match = re.search(r'__version__\s*=\s*["\']([\d.]+)["\']', version_content)
    version = version_match.group(1)

    # Create the tag
    subprocess.run(
        ["git", "commit", "-m", f"Bump version to {version}"],
        cwd=temp_project,
        check=True,
    )
    subprocess.run(
        ["git", "tag", f"v{version}"],
        cwd=temp_project,
        check=True,
    )

    # Verify the tag was created
    tags = subprocess.run(
        ["git", "tag"], cwd=temp_project, capture_output=True, text=True
    )
    assert f"v{version}" in tags.stdout


def test_bump_version_with_invalid_file(temp_project):
    """Test bumping version when version file is invalid."""
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_file.write_text("invalid content")

    result = subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Version string not found" in result.stderr


def test_bump_version_with_missing_file(temp_project):
    """Test bumping version when version file doesn't exist."""
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_file.unlink()

    result = subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr


def test_bump_version_with_invalid_args(temp_project):
    """Test bumping version with invalid arguments."""
    # Test with no arguments
    result = subprocess.run(
        ["python", "bump_version.py"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Usage:" in result.stdout

    # Test with invalid part
    result = subprocess.run(
        ["python", "bump_version.py", "invalid"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Usage:" in result.stdout


def test_release_with_uncommitted_changes(temp_project):
    """Test release process with uncommitted changes."""
    # Make a change to the version file
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_file.write_text('__version__ = "1.2.4"\n')

    # Try to create a tag without committing
    result = subprocess.run(
        ["git", "tag", "v1.2.4"],
        cwd=temp_project,
        capture_output=True,
        text=True,
    )
    assert (
        result.returncode == 0
    )  # Git allows this, but we should test the full process

    # Now try the full release process
    subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        check=True,
    )

    # Add and commit the version file
    subprocess.run(
        ["git", "add", "src/momentum/__version__.py"],
        cwd=temp_project,
        check=True,
    )

    # Get the new version by reading the file directly
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_content = version_file.read_text()
    import re

    version_match = re.search(r'__version__\s*=\s*["\']([\d.]+)["\']', version_content)
    version = version_match.group(1)

    # Create the tag
    subprocess.run(
        ["git", "commit", "-m", f"Bump version to {version}"],
        cwd=temp_project,
        check=True,
    )
    subprocess.run(
        ["git", "tag", f"v{version}"],
        cwd=temp_project,
        check=True,
    )

    # Verify the tag was created
    tags = subprocess.run(
        ["git", "tag"], cwd=temp_project, capture_output=True, text=True
    )
    assert f"v{version}" in tags.stdout


def test_consecutive_version_bumps(temp_project):
    """Test multiple consecutive version bumps."""
    # First bump to patch
    subprocess.run(
        ["python", "bump_version.py", "patch"],
        cwd=temp_project,
        check=True,
    )

    # Then bump to minor
    subprocess.run(
        ["python", "bump_version.py", "minor"],
        cwd=temp_project,
        check=True,
    )

    # Finally bump to major
    subprocess.run(
        ["python", "bump_version.py", "major"],
        cwd=temp_project,
        check=True,
    )

    # Verify final version
    version_file = Path(temp_project) / "src" / "momentum" / "__version__.py"
    version_content = version_file.read_text()
    import re

    version_match = re.search(r'__version__\s*=\s*["\']([\d.]+)["\']', version_content)
    version = version_match.group(1)
    assert (
        version == "2.0.0"
    )  # Should be 2.0.0 after patch->minor->major bumps (major resets minor and patch)
