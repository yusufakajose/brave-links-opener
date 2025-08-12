# Brave Links Opener

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
