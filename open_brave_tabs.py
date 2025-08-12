#!/usr/bin/env python3
"""
Open a list of URLs (one per line) in Brave Browser in a single window with multiple tabs.

Usage:
  python3 open_brave_tabs.py /path/to/links.txt

Options:
  --browser 
      Explicit Brave command to use (e.g., /usr/bin/brave-browser or 'flatpak run com.brave.Browser').
  --incognito
      Open in an incognito window.
  --no-new-window
      Do not force a new window; add tabs to the last active Brave window instead.

The script attempts to auto-detect Brave if --browser is not provided.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
from typing import Iterable, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open URLs from a text file in Brave in one window with multiple tabs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "links_file",
        help="Path to a text file containing one URL per line (blank lines and lines starting with '#' are ignored)",
    )
    parser.add_argument(
        "--browser",
        dest="browser_cmd",
        default=None,
        help=(
            "Explicit Brave command to run. Example: /usr/bin/brave-browser, brave, brave-browser, "
            "or 'flatpak run com.brave.Browser'"
        ),
    )
    parser.add_argument(
        "--incognito",
        action="store_true",
        help="Open URLs in an incognito window",
    )
    parser.add_argument(
        "--no-new-window",
        action="store_true",
        help="Do not force a new window; append tabs to the last active Brave window",
    )
    return parser.parse_args()


def detect_brave_command(user_specified: Optional[str]) -> List[str]:
    """Return a command list to execute Brave.

    If user_specified is provided, it is used (split via shlex). Otherwise, auto-detect
    common Brave commands on Linux (apt/snap/flatpak).
    """

    if user_specified:
        tokens = shlex.split(user_specified)
        if not tokens:
            raise SystemExit("Provided --browser command is empty")
        head = tokens[0]
        if os.path.isabs(head):
            if not os.path.exists(head):
                raise SystemExit(f"The specified browser path does not exist: {head}")
        else:
            resolved = shutil.which(head)
            if resolved is None:
                raise SystemExit(f"Could not find executable on PATH: {head}")
            tokens[0] = resolved
        return tokens

    # Candidates for native installations
    candidates = [
        "brave-browser",
        "brave",
        "brave-browser-stable",
        "brave-beta",
        "brave-nightly",
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        "/opt/brave.com/brave/brave-browser",
        "/snap/bin/brave",
    ]

    for candidate in candidates:
        if os.path.isabs(candidate):
            if os.path.exists(candidate):
                return [candidate]
        else:
            resolved = shutil.which(candidate)
            if resolved:
                return [resolved]

    # Flatpak fallback: com.brave.Browser
    flatpak = shutil.which("flatpak")
    if flatpak is not None:
        try:
            info = subprocess.run(
                [flatpak, "info", "com.brave.Browser"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=2,
            )
            if info.returncode == 0:
                return [flatpak, "run", "com.brave.Browser"]
        except Exception:
            # Ignore detection errors and continue
            pass

    raise SystemExit(
        "Could not find Brave Browser. Install it, or pass --browser with the command/path to Brave."
    )


def read_urls(links_path: str) -> List[str]:
    if not os.path.exists(links_path):
        raise SystemExit(f"Links file not found: {links_path}")

    urls: List[str] = []
    with open(links_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized = normalize_url_candidate(line)
            if normalized is None:
                # Skip lines that don't look like URLs
                continue
            urls.append(normalized)
    if not urls:
        raise SystemExit("No URLs found in the file after filtering empty/comment/invalid lines.")
    return urls


_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\.\-]*://")
_COLON_ONLY_SCHEMES = ("mailto:", "magnet:")


def normalize_url_candidate(text: str) -> Optional[str]:
    """Normalize a candidate URL string.

    - Ignore blank lines and comments (handled by caller)
    - If it already has a scheme like http://, https://, file://, mailto:, magnet:, keep as-is
    - If no scheme, default to https:// for domains, and http:// for localhost/private IPs
    """
    candidate = text.strip()
    if not candidate:
        return None

    # Already has a scheme (http://, https://, file://, etc.), or known colon-only schemes
    if candidate.startswith(_COLON_ONLY_SCHEMES) or _SCHEME_RE.match(candidate):
        return candidate

    # Prefer http for localhost and RFC1918 private ranges
    localhost_like = re.compile(
        r"^(localhost|127\.0\.0\.1|10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.(?:\d{1,3})\.(?:\d{1,3})|"
        r"172\.(?:1[6-9]|2\d|3[0-1])\.(?:\d{1,3})\.(?:\d{1,3}))(?::\d+)?(\/|$)"
    )
    if localhost_like.match(candidate):
        return f"http://{candidate}"

    # Otherwise assume https for domains/hosts
    return f"https://{candidate}"


def open_in_single_window(brave_cmd: List[str], urls: List[str], incognito: bool) -> None:
    """Open all URLs in a single new window with multiple tabs using one Brave invocation."""
    command: List[str] = list(brave_cmd)
    if incognito:
        command.append("--incognito")
    command.append("--new-window")
    command.extend(urls)

    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise SystemExit("Failed to launch Brave. Verify the command with --browser.")


def open_in_existing_window(brave_cmd: List[str], urls: List[str], incognito: bool) -> None:
    """Open URLs as new tabs in the last active Brave window.

    Note: If incognito is requested, Brave may open the first call in incognito and subsequent
    tabs will also be incognito while that window is focused.
    """
    first = True
    for url in urls:
        command: List[str] = list(brave_cmd)
        if first and incognito:
            command.append("--incognito")
        command.extend(["--new-tab", url])
        first = False
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise SystemExit("Failed to launch Brave. Verify the command with --browser.")


def main() -> None:
    args = parse_args()
    brave_cmd = detect_brave_command(args.browser_cmd)
    urls = read_urls(args.links_file)

    if args.no_new_window:
        open_in_existing_window(brave_cmd, urls, args.incognito)
    else:
        open_in_single_window(brave_cmd, urls, args.incognito)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)


