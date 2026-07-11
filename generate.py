#!/usr/bin/env python3

"""
generate.py — Markdown -> GitHub-styled, self-contained HTML page.

Reproduces the look & behaviour of exam/QA-github.html:
  * GitHub Markdown CSS (light + dark), switchable with a top-right moon/sun
    button. No FOUC: BOTH stylesheets are inlined and toggled via the `media`
    attribute (a media="not all" sheet is still parsed, just not applied).
  * A retractable Table of Contents rendered as a left sidebar drawer
    (top-left button; pushes content >=1000px, overlays with a backdrop below).
  * Output is a SINGLE self-contained file: CSS and JS are inlined, so it has
    no external dependencies and can be opened / moved anywhere.

Deterministic
  The same Markdown input + the same pandoc version always produce a
  byte-identical file: fixed flags, LF line endings, no timestamps, and the
  theme CSS is inlined verbatim from the copies stored next to this script.

Everything the generator needs lives in this folder:
  github-markdown-light.css  github-markdown-dark.css     (theme CSS)
  header.template.html  before-body.html  after-body.html (HTML partials)
  build/                                                  (intermediate files)

Requirements
  pandoc

Usage
  python generate.py INPUT.md [-o OUTPUT.html] [-t "Page title"]

  -o/--output  Output path (default: INPUT with a .html suffix).
  -t/--title   Browser-tab title (default: the first level-1 heading, else the
               input file stem). The page's own H1 remains the visible title.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"

LIGHT_CSS = HERE / "github-markdown-light.css"
DARK_CSS = HERE / "github-markdown-dark.css"
HEADER_TEMPLATE = HERE / "header.template.html"
BEFORE_BODY = HERE / "before-body.html"
AFTER_BODY = HERE / "after-body.html"

LIGHT_TOKEN = "@@GHMD_LIGHT_CSS@@"
DARK_TOKEN = "@@GHMD_DARK_CSS@@"


def die(msg: str) -> "None":
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def first_h1(markdown: str) -> str | None:
    """Return the text of the first ATX level-1 heading, sans simple markup."""
    for line in markdown.splitlines():
        m = re.match(r"^#\s+(.+?)\s*#*\s*$", line)
        if m:
            return re.sub(r"[`*_]", "", m.group(1)).strip()
    return None


def build_header(build_dir: Path) -> Path:
    """Inline the two theme stylesheets into the header partial (deterministic)."""
    header = read_text(HEADER_TEMPLATE)
    if LIGHT_TOKEN not in header or DARK_TOKEN not in header:
        die(
            f"placeholders {LIGHT_TOKEN}/{DARK_TOKEN} missing from {HEADER_TEMPLATE.name}"
        )
    # Replace tokens with the raw CSS. CSS never contains these tokens or the
    # sequence "</style>", so inlining is safe.
    header = header.replace(LIGHT_TOKEN, read_text(LIGHT_CSS).rstrip("\n"))
    header = header.replace(DARK_TOKEN, read_text(DARK_CSS).rstrip("\n"))
    if "@@GHMD_" in header:
        die(
            "an @@GHMD_*@@ placeholder is still present after inlining "
            "(a token must appear only inside the two <style> blocks, not elsewhere)"
        )
    out = build_dir / "header.inlined.html"
    out.write_text(header, encoding="utf-8")
    return out


def check_inputs() -> None:
    missing = [
        p.name
        for p in (LIGHT_CSS, DARK_CSS, HEADER_TEMPLATE, BEFORE_BODY, AFTER_BODY)
        if not p.is_file()
    ]
    if missing:
        die("missing generator asset(s): " + ", ".join(missing))
    if shutil.which("pandoc") is None:
        die("pandoc not found on PATH (install pandoc, e.g. `brew install pandoc`)")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Markdown -> GitHub-styled self-contained HTML (sidebar TOC + light/dark).",
    )
    ap.add_argument("input", help="input Markdown file")
    ap.add_argument("-o", "--output", help="output HTML file (default: INPUT.html)")
    ap.add_argument(
        "-t", "--title", help="browser-tab title (default: first H1 or file stem)"
    )
    args = ap.parse_args(argv)

    src = Path(args.input).resolve()
    if not src.is_file():
        die(f"input file not found: {src}")

    check_inputs()

    markdown = read_text(src)
    title = args.title or first_h1(markdown) or src.stem
    out = Path(args.output).resolve() if args.output else src.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)

    BUILD.mkdir(parents=True, exist_ok=True)
    header_path = build_header(BUILD)

    cmd = [
        "pandoc",
        str(src),
        "--from=markdown",
        "--to=html5",
        "--standalone",
        "--toc",
        "--toc-depth=2",
        "--syntax-highlighting=none",
        "--wrap=none",
        "--eol=lf",
        f"--metadata=pagetitle:{title}",
        "--metadata=lang:en",
        f"--include-in-header={header_path}",
        f"--include-before-body={BEFORE_BODY}",
        f"--include-after-body={AFTER_BODY}",
        f"--output={out}",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        die(f"pandoc failed with exit code {exc.returncode}")

    shutil.rmtree(BUILD)

    data = out.read_bytes()
    print(f"wrote  {out}")
    print(f"bytes  {len(data)}")
    print(f"sha256 {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
