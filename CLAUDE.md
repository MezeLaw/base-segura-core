# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (first time)
python3 -m venv .venv
source .venv/bin/activate
pip install -r basesegura_pdf/requirements.txt
playwright install chromium

# Run the CLI
source .venv/bin/activate
python -m basesegura_pdf
```

No test suite or linter is configured. The `.venv/` at the repo root uses Python 3.9.

## Architecture

`basesegura_pdf` is a CLI tool that converts BaseSegura HTML templates into filled PDFs. The flow is:

1. **`cli.py`** — interactive terminal flow: discovers templates, collects field values, invokes the engine and generator.
2. **`template_engine.py`** — pure functions (no I/O). Parses HTML with BeautifulSoup/lxml:
   - `discover_templates()` — scans `~/Documents/BaseSegura/Templates/` for `*.html` files.
   - `extract_fields()` — finds `[PLACEHOLDER]` patterns inside `.field` elements (excluding `.activity-item`/`.activity-otros`).
   - `extract_checkboxes()` — finds selectable activities (`.activity-item`, `.activity-otros`).
   - `fill_template()` — replaces placeholders, adds `checked` class + ✓ to selected activities, injects minimal CSS, removes `.legend-tip` elements, and decomposes optional sections (`data-optional-section`) whose fields are all empty.
3. **`pdf_generator.py`** — pure function. Writes the filled HTML to a temp file inside the template's directory (so relative asset paths resolve), navigates to it with Playwright Chromium headless, and calls `page.pdf()` with `prefer_css_page_size=True`.

**Key constraint:** `fill_template()` must never modify existing CSS, classes, or HTML structure — only text content in `.field` nodes, `checked` state on activity items, and the injected `<style>` append.

**Template format:** HTML files use `[LABEL: hint]` placeholders inside elements with class `field`. Multiline fields use class `block`. Activities use `.activity-item` / `.activity-otros` with a `.label-text` child and an optional `.field` child for free text.

Templates live in `~/Documents/BaseSegura/Templates/` — outside the repo.
