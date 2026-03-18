import io
import json
from unittest import mock

import pytest

from text_top_words import (
    tokenize_words,
    extract_top_words,
    process_text_from_text,
    process_file,
    save_result,
)


def test_tokenize_words_basic():
    text = "Hello, world! HELLO... 123? Abc"
    words = tokenize_words(text, min_length=2)
    assert words.count('hello') == 2
    assert words.count('world') == 1
    assert words.count('abc') == 1
    assert len(words) == 4


def test_extract_top_words_tie_breaker():
    text = "apple banana apple banana cherry"
    top = extract_top_words(text, top_n=2)
    assert top == [('apple', 2), ('banana', 2)]


def test_process_text_from_text_basic():
    text = "Hello world Hello"
    res = process_text_from_text(text, top_n=5, min_length=2)
    assert res['total_words'] == 3
    assert res['top_words'][0] == {'word': 'hello', 'count': 2}
    assert res['top_words'][1] == {'word': 'world', 'count': 1}


def test_process_file_empty():
    # Simulate empty content on every encoding attempt
    class DummyFile(io.StringIO):
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(path, mode='r', encoding=None, errors=None):
        # Fail for utf-8 and utf-8-sig, succeed with latin-1 reading empty content
        if encoding in ('utf-8', 'utf-8-sig'):
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "bad")
        return DummyFile("")

    with mock.patch('text_top_words.open', side_effect=fake_open):
        res = process_file("dummy.txt", top_n=5, min_length=2, stopwords=None)
        assert res['input_path'] == "dummy.txt"
        assert res['total_words'] == 0
        assert res['top_words'] == []


def test_process_file_with_content():
    content = "Alpha beta gamma alpha beta."

    class DummyFile(io.StringIO):
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_open(path, mode='r', encoding=None, errors=None):
        return DummyFile(content)

    with mock.patch('text_top_words.open', side_effect=fake_open):
        res = process_file("sample.txt", top_n=3, min_length=2, stopwords=None)
        assert res['input_path'] == "sample.txt"
        assert res['total_words'] == 5
        assert res['top_words'] == [
            {'word': 'alpha', 'count': 2},
            {'word': 'beta', 'count': 2},
            {'word': 'gamma', 'count': 1},
        ]


def test_save_result_writes_json():
    result = {
        "input_path": "input.txt",
        "total_words": 2,
        "top_words": [{"word": "aa", "count": 2}, {"word": "bb", "count": 0}],
        "timestamp": "2026-01-01T00:00:00Z",
        "notes": {"stopwords_removed": False, "min_length": 2},
    }

    opened = []

    def fake_open(path, mode='w', encoding=None):
        f = io.StringIO()
        opened.append((path, f))
        return f

    with mock.patch('text_top_words.open', side_effect=fake_open), \
         mock.patch('text_top_words.os.path.exists', return_value=True), \
         mock.patch('text_top_words.os.path.abspath', side_effect=lambda p: '/fake_dir/' + p):
        save_result(result, "output/result.json")
        assert opened, "No file was opened by save_result"
        path_used, fobj = opened[-1]
        expected = json.dumps(result, indent=4, ensure_ascii=False)
        assert fobj.getvalue() == expected
