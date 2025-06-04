"""Tests for Pomodoro timer functionality."""

from unittest.mock import patch, MagicMock
from momentum.timer import PomodoroTimer, cmd_timer
from momentum.display import create_progress_bar, format_time


class TestPomodoroTimer:
    def test_timer_initialization(self):
        """Test timer initializes with correct values."""
        timer = PomodoroTimer(25, 5)
        assert timer.work_duration == 1500  # 25 * 60
        assert timer.break_duration == 300  # 5 * 60
        assert timer.current_phase == "work"
        assert not timer.is_running

    def test_timer_default_break(self):
        """Test timer uses default break time."""
        timer = PomodoroTimer(30)
        assert timer.work_duration == 1800
        assert timer.break_duration == 300  # default 5 minutes

    @patch("time.sleep")
    @patch("builtins.print")
    def test_countdown_display(self, mock_print, mock_sleep):
        """Test countdown displays correct format."""
        timer = PomodoroTimer(1)  # 1 minute
        timer._countdown(3, "work")  # 3 seconds, work phase

        # Should print 00:03, 00:02, 00:01, 00:00, and a newline, plus clear_line prints
        assert mock_print.call_count == 9
        mock_sleep.assert_called_with(1)

    def test_cmd_timer_args(self):
        """Test cmd_timer processes arguments correctly."""
        args = MagicMock()
        args.work_minutes = 25
        args.break_minutes = 10
        args.plain = False  # Ensure plain is set to a boolean

        with patch("momentum.timer.PomodoroTimer") as mock_timer:
            cmd_timer(args)
            mock_timer.assert_called_once_with(25, 10, False)


class TestDisplayUtilities:
    def test_progress_bar_creation(self):
        """Test progress bar creation."""
        # 50% progress
        bar = create_progress_bar(30, 60, width=10)
        assert "█████░░░░░" in bar
        assert "50%" in bar

    def test_time_formatting(self):
        """Test time formatting."""
        assert format_time(125) == "02:05"
        assert format_time(3661) == "61:01"
        assert format_time(59) == "00:59"
