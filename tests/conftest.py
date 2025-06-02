"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

# Import the module under test
from momentum import momentum


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / "test_storage.json"

    # Patch the global STORE variable
    original_store = momentum.STORE
    momentum.STORE = temp_file

    yield temp_file

    # Cleanup
    momentum.STORE = original_store
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_data():
    """Sample data structure for testing."""
    return {
        "backlog": [
            {"task": "Old backlog task", "ts": "2025-05-29T10:00:00"},
            {"task": "Recent backlog task", "ts": "2025-05-30T14:30:00"},
        ],
        "2025-05-30": {
            "todo": "Current active task",
            "done": [
                {
                    "id": "abc12345",
                    "task": "Completed task",
                    "ts": "2025-05-30T09:15:30",
                }
            ],
        },
    }


@pytest.fixture
def empty_data():
    """Empty data structure for testing fresh starts."""
    return {}


@pytest.fixture
def plain_mode():
    """Enable plain mode for consistent test output."""
    original_plain = momentum.USE_PLAIN
    momentum.USE_PLAIN = True
    yield
    momentum.USE_PLAIN = original_plain


@pytest.fixture
def mock_datetime():
    """Mock datetime.now() for consistent timestamps."""
    with patch("momentum.momentum.datetime") as mock_dt:
        mock_now = mock_dt.now.return_value
        mock_now.isoformat.return_value = "2025-05-30T12:00:00"
        yield mock_dt
