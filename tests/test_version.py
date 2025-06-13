import pytest
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch

# Import the version management functions
sys.path.append(str(Path(__file__).parent.parent))
from bump_version import get_current_version, bump, set_version


@pytest.fixture
def version_file():
    """Create a temporary version file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as f:
        f.write('__version__ = "1.2.3"\n')
        f.flush()
        yield Path(f.name)


def test_get_current_version(version_file):
    """Test getting the current version from a file."""
    with patch("bump_version.VERSION_FILE", version_file):
        assert get_current_version() == "1.2.3"


def test_bump_major():
    """Test bumping major version."""
    assert bump("1.2.3", "major") == "2.0.0"
    assert bump("0.1.0", "major") == "1.0.0"


def test_bump_minor():
    """Test bumping minor version."""
    assert bump("1.2.3", "minor") == "1.3.0"
    assert bump("0.1.0", "minor") == "0.2.0"


def test_bump_patch():
    """Test bumping patch version."""
    assert bump("1.2.3", "patch") == "1.2.4"
    assert bump("0.1.0", "patch") == "0.1.1"


def test_bump_invalid_part():
    """Test that invalid version part raises ValueError."""
    with pytest.raises(ValueError, match="part must be one of: major, minor, patch"):
        bump("1.2.3", "invalid")


def test_set_version(version_file):
    """Test setting a new version in the file."""
    with patch("bump_version.VERSION_FILE", version_file):
        set_version("2.0.0")
        assert version_file.read_text().strip() == '__version__ = "2.0.0"'


def test_get_current_version_invalid_format(version_file):
    """Test getting version from file with invalid format."""
    version_file.write_text("invalid content")
    with patch("bump_version.VERSION_FILE", version_file):
        with pytest.raises(ValueError, match="Version string not found"):
            get_current_version()
