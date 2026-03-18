import text_top_words as tt


def test_tie_break_order():
    text = "brown brown the the dog fox jumps"
    top = tt.extract_top_words(text, top_n=5)
    assert top == [("brown", 2), ("the", 2), ("dog", 1), ("fox", 1), ("jumps", 1)]


def test_process_text_from_text_returns_expected():
    text = "brown brown the the dog fox jumps"
    res = tt.process_text_from_text(text, top_n=5)
    assert res["total_words"] == 7
    assert res["top_words"] == [
        {"word": "brown", "count": 2},
        {"word": "the", "count": 2},
        {"word": "dog", "count": 1},
        {"word": "fox", "count": 1},
        {"word": "jumps", "count": 1},
    ]
    assert res["input_path"] is None


def test_empty_text():
    res = tt.process_text_from_text("", top_n=5)
    assert res["total_words"] == 0
    assert res["top_words"] == []
