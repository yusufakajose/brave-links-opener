import types
from typing import List

import pytest

import open_brave_tabs as mod


def test_normalize_url_candidate_scheme_passthrough():
    url = "https://example.com/path?a=1"
    assert mod.normalize_url_candidate(url) == url


def test_normalize_url_candidate_default_schemes():
    assert mod.normalize_url_candidate("example.com") == "https://example.com"
    assert mod.normalize_url_candidate("example.com/path") == "https://example.com/path"
    assert mod.normalize_url_candidate("localhost:8080") == "http://localhost:8080"
    assert mod.normalize_url_candidate("192.168.1.10") == "http://192.168.1.10"
    assert mod.normalize_url_candidate("") is None


def test_read_urls_basic(tmp_path):
    links = "\n".join(
        [
            "",  # blank
            "# a comment",  # comment
            "example.com",
            "https://baz.com/x",
            "localhost:1234",
            "10.0.0.10",
            "   ",  # whitespace
        ]
    )
    p = tmp_path / "links.txt"
    p.write_text(links, encoding="utf-8")

    urls = mod.read_urls(str(p))
    assert urls == [
        "https://example.com",
        "https://baz.com/x",
        "http://localhost:1234",
        "http://10.0.0.10",
    ]


def test_read_urls_missing_file():
    with pytest.raises(SystemExit) as exc:
        mod.read_urls("/nonexistent/file/xyz.txt")
    assert "Links file not found" in str(exc.value)


def test_read_urls_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        mod.read_urls(str(p))
    assert "No URLs found" in str(exc.value)


def test_detect_brave_command_user_specified_absolute(monkeypatch):
    # Simulate an existing absolute path
    monkeypatch.setattr(mod.os.path, "exists", lambda path: True)
    cmd = mod.detect_brave_command("/custom/brave-browser --flag")
    assert cmd[0] == "/custom/brave-browser"
    assert "--flag" in cmd


def test_detect_brave_command_user_specified_on_path(monkeypatch):
    # Simulate resolving from PATH
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/brave" if name == "brave" else None)
    cmd = mod.detect_brave_command("brave --arg")
    assert cmd[0] == "/usr/bin/brave"
    assert "--arg" in cmd


def test_detect_brave_command_auto_flatpak(monkeypatch):
    # No native candidates, but flatpak is present and app is installed
    monkeypatch.setattr(mod.os.path, "exists", lambda path: False)

    def fake_which(name: str):
        if name == "flatpak":
            return "/usr/bin/flatpak"
        return None

    monkeypatch.setattr(mod.shutil, "which", fake_which)

    class Result:
        def __init__(self, returncode: int):
            self.returncode = returncode

    def fake_run(args: List[str], **kwargs):
        # Expect: [flatpak, "info", "com.brave.Browser"]
        if len(args) >= 3 and args[1] == "info" and args[2] == "com.brave.Browser":
            return Result(0)
        return Result(1)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    cmd = mod.detect_brave_command(None)
    assert cmd == ["/usr/bin/flatpak", "run", "com.brave.Browser"]


def test_detect_brave_command_failure(monkeypatch):
    monkeypatch.setattr(mod.os.path, "exists", lambda path: False)
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        mod.detect_brave_command(None)
    assert "Could not find Brave Browser" in str(exc.value)


def test_open_in_single_window_invocation(monkeypatch):
    calls = []

    def fake_popen(args, stdout=None, stderr=None):
        calls.append(list(args))
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr(mod.subprocess, "Popen", fake_popen)

    mod.open_in_single_window(["brave"], ["https://a", "https://b"], incognito=True)
    assert len(calls) == 1
    assert calls[0][:3] == ["brave", "--incognito", "--new-window"]
    assert calls[0][-2:] == ["https://a", "https://b"]


def test_open_in_existing_window_invocation(monkeypatch):
    calls = []

    def fake_popen(args, stdout=None, stderr=None):
        calls.append(list(args))
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr(mod.subprocess, "Popen", fake_popen)

    mod.open_in_existing_window(["brave"], ["https://a", "https://b"], incognito=True)
    assert calls[0] == ["brave", "--incognito", "--new-tab", "https://a"]
    assert calls[1] == ["brave", "--new-tab", "https://b"]


