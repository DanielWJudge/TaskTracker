"""Tests for storage operations."""

import json
from unittest.mock import patch
from momentum import load, save, ensure_today, get_backlog
import os


class TestLoad:
    """Test the load function."""

    def test_load_existing_file(self, temp_storage, sample_data):
        """Test loading existing valid file."""
        temp_storage.write_text(json.dumps(sample_data), encoding="utf-8")
        result = load()
        # Migrate sample_data for comparison
        expected = json.loads(json.dumps(sample_data))
        if "backlog" in expected:
            for task in expected["backlog"]:
                if isinstance(task, dict) and "state" not in task:
                    task["state"] = "active"
        assert result == expected

    def test_load_nonexistent_file(self, temp_storage):
        """Test loading when file doesn't exist."""
        result = load()
        assert result == {}

    def test_load_corrupted_json(self, temp_storage, capsys):
        """Test loading corrupted JSON file."""
        temp_storage.write_text("invalid json content", encoding="utf-8")
        result = load()

        assert result == {}  # Should return empty dict
        captured = capsys.readouterr()
        assert "Storage file corrupted" in captured.out
        assert "Creating backup" in captured.out

        # Check that backup was created
        backup_file = temp_storage.with_suffix(".json.backup")
        assert backup_file.exists()
        assert backup_file.read_text() == "invalid json content"

    @patch("momentum.STORE")
    def test_load_permission_error(self, mock_store, capsys):
        """Test loading with permission error."""
        mock_store.exists.return_value = True
        mock_store.read_text.side_effect = PermissionError("Access denied")

        result = load()
        assert result == {}

        captured = capsys.readouterr()
        assert "Cannot read storage file" in captured.out


class TestSave:
    """Test the save function."""

    def test_save_success(self, temp_storage, sample_data):
        """Test successful save operation."""
        result = save(sample_data)
        assert result is True

        # Verify file was written correctly
        saved_data = json.loads(temp_storage.read_text(encoding="utf-8"))
        assert saved_data == sample_data

    @patch("momentum.STORE")
    def test_save_permission_error(self, mock_store, capsys):
        """Test save with permission error."""
        mock_store.write_text.side_effect = PermissionError("Access denied")

        result = save({"test": "data"})
        assert result is False

        captured = capsys.readouterr()
        assert "Cannot save to storage file" in captured.out

    def test_save_serialization_error(self, temp_storage, capsys):
        """Test save with non-serializable data."""
        # Create non-serializable data
        non_serializable = {"func": lambda x: x}

        result = save(non_serializable)
        assert result is False

        captured = capsys.readouterr()
        assert "Data serialization error" in captured.out


class TestDataStructure:
    """Test data structure helper functions."""

    def test_ensure_today_new_data(self, mock_datetime):
        """Test ensure_today with empty data."""
        old_env = os.environ.get("MOMENTUM_TODAY_KEY")
        os.environ["MOMENTUM_TODAY_KEY"] = "2025-05-30"
        try:
            data = {}
            today = ensure_today(data)
            assert "backlog" in data
            assert data["backlog"] == []
            assert "2025-05-30" in data  # mocked date
            assert today["todo"] is None
            assert today["done"] == []
        finally:
            if old_env is not None:
                os.environ["MOMENTUM_TODAY_KEY"] = old_env
            else:
                del os.environ["MOMENTUM_TODAY_KEY"]

    def test_ensure_today_existing_data(self, sample_data):
        """Test ensure_today with existing data."""
        old_env = os.environ.get("MOMENTUM_TODAY_KEY")
        os.environ["MOMENTUM_TODAY_KEY"] = "2025-05-30"
        try:
            original_backlog = sample_data["backlog"].copy()
            today = ensure_today(sample_data)
            # Should preserve existing backlog
            assert sample_data["backlog"] == original_backlog
            assert today["todo"] == "Current active task"
        finally:
            if old_env is not None:
                os.environ["MOMENTUM_TODAY_KEY"] = old_env
            else:
                del os.environ["MOMENTUM_TODAY_KEY"]

    def test_get_backlog_new_data(self):
        """Test get_backlog creates backlog if missing."""
        data = {}
        backlog = get_backlog(data)

        assert backlog == []
        assert data["backlog"] == []

    def test_get_backlog_existing_data(self, sample_data):
        """Test get_backlog returns existing backlog."""
        backlog = get_backlog(sample_data)
        assert len(backlog) == 2
        assert backlog[0]["task"] == "Old backlog task"
