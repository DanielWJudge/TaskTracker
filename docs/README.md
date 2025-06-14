# Documentation for Momentum

## Building Locally

```bash
cd docs
make html
```

Open `build/html/index.html` in your browser.

## Man Page Generation

```bash
cd docs
make man
```

The man page will be in `build/man/`.

## Adding Screenshots/GIFs

Place images in `docs/_static/` and reference them in Markdown or reStructuredText files.

## Notes
- All code examples should be tested and up-to-date.
- Use MyST Markdown for new docs.
- API docs are generated from Python docstrings.
