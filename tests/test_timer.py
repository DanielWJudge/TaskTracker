"""Tests for Pomodoro timer functionality."""

from unittest.mock import patch, MagicMock
from momentum.timer import PomodoroTimer, cmd_timer
from momentum.display import create_progress_bar, format_time
import pytest


class TestPomodoroTimer:
    def test_timer_initialization(self):
        """Test timer initializes with correct work and break durations."""
        timer = PomodoroTimer(25, 10)
        assert timer.work_duration == 1500  # 25 minutes in seconds
        assert timer.break_duration == 600  # 10 minutes in seconds
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

    def test_timer_respects_global_flags(self):
        """Test timer respects --plain flag."""
        args = MagicMock()
        args.work_minutes = 25
        args.break_minutes = 10
        args.plain = True  # Set plain mode to True

        with patch("momentum.timer.PomodoroTimer") as mock_timer:
            cmd_timer(args)
            mock_timer.assert_called_once_with(25, 10, True)

    @patch("signal.signal")
    @patch("sys.exit")
    def test_timer_cancellation(self, mock_exit, mock_signal):
        """Test timer can be cancelled and handles cancellation gracefully."""
        timer = PomodoroTimer(25, 10)
        timer._handle_cancel(None, None)
        assert not timer.is_running
        mock_exit.assert_called_once_with(0)

    @patch("momentum.timer.PomodoroTimer._countdown")
    @patch("builtins.print")
    def test_timer_completion(self, mock_print, mock_countdown):
        """Test timer completes both work and break sessions."""
        timer = PomodoroTimer(25, 5)
        timer.start()

        # Verify work session was run
        mock_print.assert_any_call("🍅 WORK SESSION (25 minutes)")
        mock_countdown.assert_any_call(1500, "work")  # 25 minutes in seconds
        mock_print.assert_any_call("\n✅ Work session complete!")

        # Verify break session was run
        mock_print.assert_any_call("☕ BREAK TIME (5 minutes)")
        mock_countdown.assert_any_call(300, "break")  # 5 minutes in seconds
        mock_print.assert_any_call("\n🎉 Break complete!")

    def test_very_short_duration(self):
        """Test timer works with very short durations."""
        timer = PomodoroTimer(0, 0)  # 0 minutes for both work and break
        assert timer.work_duration == 0
        assert timer.break_duration == 0

    def test_very_long_duration(self):
        """Test timer handles very long durations."""
        timer = PomodoroTimer(999, 999)  # 999 minutes for both work and break
        assert timer.work_duration == 59940  # 999 * 60
        assert timer.break_duration == 59940

    def test_invalid_duration_type(self):
        """Test timer handles invalid duration types."""
        with pytest.raises(TypeError):
            PomodoroTimer("25", "5")  # Strings instead of integers

    def test_negative_duration(self):
        """Test timer handles negative durations."""
        with pytest.raises(ValueError):
            PomodoroTimer(-25, -5)  # Negative durations


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
