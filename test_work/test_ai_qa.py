import json
from pathlib import Path
import pytest

from utils.word_top_words import (
    tokenize,
    count_top_n,
    analyze_text,
    load_text_from_file,
    save_results,
    EmptyTextError,
    InputReadError,
    OutputWriteError,
)


def test_tokenize_basic():
    text = "Hello, world! It's a test."
    tokens = tokenize(text)
    assert tokens == ["hello", "world", "it's", "a", "test"]


def test_count_top_n_tie_break():
    words = ["a", "b", "a", "b", "c", "d"]
    top = count_top_n(words, top_n=2)
    assert top == [{"word": "a", "count": 2}, {"word": "b", "count": 2}]


def test_analyze_text_empty_raises():
    with pytest.raises(EmptyTextError):
        analyze_text("")


def test_analyze_text_normal_flow():
    text = "apple banana apple orange banana apple"
    res = analyze_text(text, top_n=5)
    assert res == [
        {"word": "apple", "count": 3},
        {"word": "banana", "count": 2},
        {"word": "orange", "count": 1},
    ]


def test_load_text_from_file_utf8(tmp_path):
    content = "This is UTF8."
    p = tmp_path / "utf8.txt"
    p.write_text(content, encoding="utf-8")
    text = load_text_from_file(p)
    assert text == content


def test_load_text_from_file_fallback_encoding_latin1(tmp_path):
    # Create a latin-1 encoded file containing a non-utf-8 sequence
    p = tmp_path / "latin1.txt"
    p.write_bytes("café".encode("latin-1"))
    text = load_text_from_file(p)
    assert text == "café"


def test_load_text_from_file_not_found():
    with pytest.raises(InputReadError):
        load_text_from_file("nonexistent_file_for_tests.txt")


def test_save_results_writes_json_and_content(tmp_path):
    out = tmp_path / "results" / "result.json"
    results = [{"word": "example", "count": 42}, {"word": "text", "count": 21}]
    save_results(results, out, top_n=5)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["top_n"] == 5
    assert data["top_words"] == results


def test_save_results_permission_error(monkeypatch, tmp_path):
    out = tmp_path / "restricted" / "result.json"
    import pathlib
    original_mkdir = pathlib.Path.mkdir

    def fake_mkdir(self, *args, **kwargs):
        raise PermissionError("no perm")

    monkeypatch.setattr(pathlib.Path, "mkdir", fake_mkdir, raising=True)
    try:
        with pytest.raises(OutputWriteError):
            save_results([{"word": "a", "count": 1}], out, top_n=1)
    finally:
        monkeypatch.setattr(pathlib.Path, "mkdir", original_mkdir, raising=True)


def test_load_text_from_file_permission_error(monkeypatch, tmp_path):
    p = tmp_path / "perm.txt"
    p.write_text("abc", encoding="utf-8")
    import pathlib

    def open_raises(self, mode="r", encoding=None):
        raise OSError("perm")

    with monkeypatch.context() as m:
        m.setattr(pathlib.Path, "open", open_raises, raising=True)
        with pytest.raises(InputReadError):
            load_text_from_file(p)
