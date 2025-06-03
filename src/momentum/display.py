"""Display utilities for Momentum."""


def create_progress_bar(
    current: int, total: int, width: int = 25, plain_mode: bool = False
) -> str:
    """Create a progress bar string."""
    if total == 0:
        percentage = 0.0
    else:
        percentage = (total - current) / total

    filled_width = int(percentage * width)

    if plain_mode:
        filled_char = "█"
        empty_char = "░"
    else:
        filled_char = "█"
        empty_char = "░"

    bar = filled_char * filled_width + empty_char * (width - filled_width)
    return f"{bar} {percentage*100:3.0f}%"


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def clear_line():
    """Clear current line for updating display."""
    print("\r" + " " * 80 + "\r", end="", flush=True)


def print_timer_status(
    phase: str, time_remaining: int, total_time: int, plain_mode: bool = False
):
    """Print formatted timer status."""
    time_str = format_time(time_remaining)
    total_str = format_time(total_time)
    progress = create_progress_bar(time_remaining, total_time, plain_mode=plain_mode)

    if plain_mode:
        phase_indicator = f"[{phase.upper()}]"
    else:
        phase_indicator = "🍅 WORK SESSION" if phase == "work" else "☕ BREAK TIME"

    status_line = f"{phase_indicator} ({total_str}) | {progress} | {time_str} remaining"

    clear_line()
    print(f"\r{status_line}", end="", flush=True)
