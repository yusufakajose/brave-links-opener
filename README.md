# Brave Links Opener

[![CI](https://github.com/yusufakajose/brave-links-opener/actions/workflows/ci.yml/badge.svg)](https://github.com/yusufakajose/brave-links-opener/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Open URLs from a text file in Brave Browser in a single window with multiple tabs.

## Features
- Open all links in one Brave window as separate tabs
- Optional incognito and "add to existing window" modes
- Autodetects Brave (deb/snap/flatpak)
- Ignores blank and commented lines; normalizes links without scheme (adds https:// or http:// for localhost)

## Requirements
- Python 3.8+
- Brave Browser installed

## Usage
```bash
python3 open_brave_tabs.py /path/to/links.txt
```

### Options
- `--browser` Specify Brave command (e.g., `/usr/bin/brave-browser`, `brave`, or `flatpak run com.brave.Browser`).
- `--incognito` Open in an incognito window.
- `--no-new-window` Add tabs to the last active window instead of opening a new one.

### Examples
```bash
# Open in a new window
python3 open_brave_tabs.py links.txt

# Incognito
python3 open_brave_tabs.py links.txt --incognito

# Flatpak installation
python3 open_brave_tabs.py links.txt --browser "flatpak run com.brave.Browser"

# Add to the last active window
python3 open_brave_tabs.py links.txt --no-new-window
```

### Input format
- One URL per line
- Lines starting with `#` and blank lines are ignored
- Lines without a scheme are prefixed with `https://` (or `http://` for localhost/private IPs)

Example: see `examples/links.txt`.
 
## Testing

This repository includes a small pytest suite.

### Run tests locally
Option A (virtual environment):
```bash
sudo apt install -y python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Option B (system Python user install):
```bash
python3 -m pip install --user pytest
python3 -m pytest -q
```

### Continuous Integration
GitHub Actions runs the test suite on push/PR for Python 3.8 and 3.12 via `.github/workflows/ci.yml`.