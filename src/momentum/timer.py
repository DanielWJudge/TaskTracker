"""Pomodoro timer functionality for Momentum."""

import time
import signal
import sys
from .display import print_timer_status


class PomodoroTimer:
    """
    Pomodoro timer for work/break intervals.

    Args:
        work_minutes (int): Duration of work session in minutes.
        break_minutes (int, optional): Duration of break in minutes. Defaults to 5.
        plain_mode (bool, optional): If True, disables emoji/color output.

    Raises:
        TypeError: If durations are not integers.
        ValueError: If durations are negative.
    """

    def __init__(
        self, work_minutes: int, break_minutes: int = 5, plain_mode: bool = False
    ):
        """
        Initialize PomodoroTimer with validation.

        Args:
            work_minutes (int): Duration of work session in minutes.
            break_minutes (int, optional): Duration of break in minutes. Defaults to 5.
            plain_mode (bool, optional): If True, disables emoji/color output.

        Raises:
            TypeError: If durations are not integers.
            ValueError: If durations are negative.
        """
        if not isinstance(work_minutes, int) or not isinstance(break_minutes, int):
            raise TypeError("Work and break durations must be integers")

        if work_minutes < 0 or break_minutes < 0:
            raise ValueError("Work and break durations cannot be negative")

        self.work_duration = work_minutes * 60
        self.break_duration = break_minutes * 60
        self.is_running = False
        self.current_phase = "work"  # "work" or "break"
        self.time_remaining = self.work_duration
        self.plain_mode = plain_mode

    def start(self):
        """
        Start the timer with basic output.

        Handles SIGINT for graceful cancellation and runs both work and break sessions.
        """
        self.is_running = True
        signal.signal(signal.SIGINT, self._handle_cancel)

        try:
            self._run_work_session()
            self._run_break_session()
        except KeyboardInterrupt:
            self._handle_cancel(None, None)

    def _run_work_session(self):
        """Run work session with basic countdown."""
        print(f"🍅 WORK SESSION ({self.work_duration // 60} minutes)")
        self._countdown(self.work_duration, "work")
        print("\n✅ Work session complete!")

    def _run_break_session(self):
        """Run break session with basic countdown."""
        print(f"☕ BREAK TIME ({self.break_duration // 60} minutes)")
        self._countdown(self.break_duration, "break")
        print("\n🎉 Break complete!")

    def _countdown(self, duration: int, phase: str):
        """Enhanced countdown with progress bar."""
        for remaining in range(duration, -1, -1):  # Include 0 in the countdown
            print_timer_status(phase, remaining, duration, self.plain_mode)
            if remaining > 0:  # Only sleep if there's time remaining
                time.sleep(1)
        print()  # New line after completion

    def _handle_cancel(self, signum, frame):
        """Handle timer cancellation."""
        print("\n⏹️  Timer cancelled")
        self.is_running = False
        sys.exit(0)


def cmd_timer(args):
    """Command function for timer."""
    plain_mode = getattr(args, "plain", False)
    timer = PomodoroTimer(args.work_minutes, args.break_minutes, plain_mode)
    timer.start()
