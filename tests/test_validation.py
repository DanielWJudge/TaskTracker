"""Tests for input validation functions."""

from unittest.mock import patch
from momentum.cli import validate_task_name, safe_input, safe_int_input, Config


class TestValidateTaskName:
    """Test the validate_task_name function."""

    def test_valid_task_names(self):
        """Test valid task names."""
        valid_names = [
            "Simple task",
            "Task with numbers 123",
            "Task-with-dashes",
            "Task_with_underscores",
            "Task with émojis 🎉",
            "A" * Config.MAX_TASK_LENGTH,  # exactly at limit
        ]

        for name in valid_names:
            is_valid, error = validate_task_name(name)
            assert is_valid, f"'{name}' should be valid, got error: {error}"
            assert error == ""

    def test_invalid_task_names(self):
        """Test invalid task names."""
        invalid_cases = [
            ("", "Task name cannot be empty."),
            (None, "Task name cannot be empty."),
            ("   ", "Task name cannot be only whitespace."),
            ("\t\n", "Task name cannot be only whitespace."),
            ("Task\nwith\nlines", "Task name cannot contain line breaks."),
            ("Task\rwith\rcarriage", "Task name cannot contain line breaks."),
            (
                "A" * (Config.MAX_TASK_LENGTH + 1),
                f"Task name too long (max {Config.MAX_TASK_LENGTH} characters).",
            ),
        ]

        for name, expected_error in invalid_cases:
            is_valid, error = validate_task_name(name)
            assert not is_valid, f"'{name}' should be invalid"
            assert error == expected_error

    def test_whitespace_trimming_awareness(self):
        """Test that validation considers trimmed length."""
        # Task that's valid after trimming
        is_valid, error = validate_task_name("  Valid task  ")
        assert is_valid
        assert error == ""

        # Task that's too long even after trimming
        long_task = "  " + "A" * (Config.MAX_TASK_LENGTH + 1) + "  "
        is_valid, error = validate_task_name(long_task)
        assert not is_valid
        assert "too long" in error


class TestSafeInput:
    """Test the safe_input function."""

    @patch("builtins.input")
    def test_valid_input(self, mock_input):
        """Test normal input flow."""
        mock_input.return_value = "  test input  "
        result = safe_input("Enter something: ")
        assert result == "test input"  # should be stripped

    @patch("builtins.input")
    def test_input_with_validator(self, mock_input):
        """Test input with validation function."""
        mock_input.return_value = "valid task"
        result = safe_input("Enter task: ", validate_task_name)
        assert result == "valid task"

    @patch("builtins.input")
    def test_input_with_failed_validation(self, mock_input, capsys):
        """Test input that fails validation."""
        mock_input.return_value = ""  # empty task
        result = safe_input("Enter task: ", validate_task_name)
        assert result is None

        captured = capsys.readouterr()
        assert "Task name cannot be empty" in captured.out

    @patch("builtins.input")
    def test_keyboard_interrupt(self, mock_input, capsys):
        """Test handling of keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()
        result = safe_input("Enter something: ")
        assert result is None

        captured = capsys.readouterr()
        assert "Input cancelled" in captured.out


class TestSafeIntInput:
    """Test the safe_int_input function."""

    @patch("builtins.input")
    def test_valid_integer(self, mock_input):
        """Test valid integer input."""
        mock_input.return_value = "42"
        result = safe_int_input("Enter number: ")
        assert result == 42

    @patch("builtins.input")
    def test_integer_with_bounds(self, mock_input):
        """Test integer input with min/max validation."""
        mock_input.return_value = "5"
        result = safe_int_input("Enter 1-10: ", min_val=1, max_val=10)
        assert result == 5

    @patch("builtins.input")
    def test_integer_below_minimum(self, mock_input, capsys):
        """Test integer below minimum."""
        mock_input.return_value = "0"
        result = safe_int_input("Enter 1-10: ", min_val=1, max_val=10)
        assert result is None

        captured = capsys.readouterr()
        assert "must be at least 1" in captured.out

    @patch("builtins.input")
    def test_integer_above_maximum(self, mock_input, capsys):
        """Test integer above maximum."""
        mock_input.return_value = "15"
        result = safe_int_input("Enter 1-10: ", min_val=1, max_val=10)
        assert result is None

        captured = capsys.readouterr()
        assert "must be at most 10" in captured.out

    @patch("builtins.input")
    def test_non_integer_input(self, mock_input, capsys):
        """Test non-integer input."""
        mock_input.return_value = "not a number"
        result = safe_int_input("Enter number: ")
        assert result is None

        captured = capsys.readouterr()
        assert "Must be a number" in captured.out

    @patch("builtins.input")
    def test_empty_input(self, mock_input):
        """Test empty input returns None."""
        mock_input.return_value = ""
        result = safe_int_input("Enter number: ")
        assert result is None
