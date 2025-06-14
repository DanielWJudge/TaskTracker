# Troubleshooting

Having issues with Momentum? Here are solutions to common problems.

## Command Not Found
If you see:

```
command not found: momentum
```

- Make sure you installed Momentum with `pip install momentum`.
- If using a virtual environment, ensure it is activated.
- Try running with `python -m momentum` if the executable is not in your PATH.

## No Module Named 'momentum'
If you see:

```
ModuleNotFoundError: No module named 'momentum'
```

- Ensure your `PYTHONPATH` includes the correct source directory if running from source.
- Run from the project root or set `PYTHONPATH`:
  ```bash
  export PYTHONPATH=$(pwd)/src
  python -m momentum status
  ```

## Unicode/Emoji Issues
If output looks strange or you see encoding errors:
- Try running with the `--plain` flag to disable emoji and color:
  ```bash
  momentum status --plain
  ```

## Still Stuck?
- Check the [GitHub Issues](https://github.com/your-username/momentum/issues) for help or to report a bug.
- Include your OS, Python version, and the exact error message when asking for support.
