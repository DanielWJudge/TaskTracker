"""Tests for Pomodoro timer functionality."""

from unittest.mock import patch, MagicMock
from momentum.timer import PomodoroTimer, cmd_timer


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
        timer._countdown(3)  # 3 seconds

        # Should print 00:03, 00:02, 00:01
        assert mock_print.call_count == 3
        mock_sleep.assert_called_with(1)

    def test_cmd_timer_args(self):
        """Test cmd_timer processes arguments correctly."""
        args = MagicMock()
        args.work_minutes = 25
        args.break_minutes = 10

        with patch("momentum.timer.PomodoroTimer") as mock_timer:
            cmd_timer(args)
            mock_timer.assert_called_once_with(25, 10)
