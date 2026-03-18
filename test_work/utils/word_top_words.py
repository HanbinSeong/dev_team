from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Union
from collections import Counter


# Public Exceptions
class EmptyTextError(Exception):
    """Raised when there is no valid text to analyze."""


class InputReadError(Exception):
    """Raised when reading the input text (from string or file) fails."""


class OutputWriteError(Exception):
    """Raised when writing the output JSON fails."""


# Tokenization

def tokenize(text: str) -> List[str]:
    """Tokenize English text into lowercased words.

    - Converts to lowercase
    - Extracts sequences that consist of a-z and apostrophes
    - Filters out tokens that do not contain any alphabetic character
    - Returns list of words
    
    Note: Apostrophes are allowed to support simple contractions like don't, it's, etc.
    """
    if text is None:
        return []
    text = text.lower()
    # [a-z']+ matches letters and apostrophes; keep only tokens with at least one letter
    tokens = [t for t in re.findall(r"[a-z']+", text) if re.search(r"[a-z]", t)]
    return tokens


def count_top_n(words: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
    """Count word frequencies and return the top_n words sorted by
    (descending count, ascending word).
    Returns a list of dicts: [{"word": ..., "count": ...}, ...]
    """
    if not words:
        return []
    counts = Counter(words)
    # Sort by (-count, word) to handle ties alphabetically
    sorted_items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = sorted_items[:top_n]
    return [{"word": w, "count": c} for w, c in top]


def analyze_text(text: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """High-level analyze function: tokenize text and return top_n words.

    Raises EmptyTextError if there are no valid words in the input text.
    """
    if text is None:
        raise EmptyTextError("Input text is empty or None.")
    tokens = tokenize(text)
    if not tokens:
        raise EmptyTextError("Input text contains no valid words after tokenization.")
    return count_top_n(tokens, top_n)


def _to_path(input_path: Union[str, Path]) -> Path:
    return Path(input_path) if not isinstance(input_path, Path) else input_path


def load_text_from_file(path: Union[str, Path]) -> str:
    """Read text from a file with encoding fallbacks.

    Tries encodings in order: utf-8, latin-1, cp1252. If the file does not exist,
    raises InputReadError. If decoding fails for all encodings, also raises
    InputReadError.
    """
    p = _to_path(path)
    if not p.exists():
        raise InputReadError(f"Input file not found: {p}")

    encodings = ["utf-8", "latin-1", "cp1252"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            with p.open("r", encoding=enc) as f:
                data = f.read()
            return data
        except UnicodeDecodeError as e:
            last_err = e
            continue
        except OSError as e:
            # Permission denied or other I/O errors
            raise InputReadError(f"Failed to read input file {p}. Reason: {e}") from e

    # If we reach here, all encodings failed to decode
    raise InputReadError(
        f"Failed to decode input file {p} with tried encodings: {', '.join(encodings)}."
    ) from last_err


def save_results(results: List[Dict[str, Any]], output_path: Union[str, Path], top_n: int = 5) -> None:
    """Save the analysis results into a pretty JSON file.

    The output JSON has the schema:
    {
        "top_words": [ {"word": ..., "count": ...}, ... ],
        "top_n": <int>
    }
    """
    payload = {
        "top_words": results,
        "top_n": top_n,
    }

    path = _to_path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise OutputWriteError(
            f"Failed to create directory for output: {path.parent}. Reason: {e}"
        ) from e

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
            f.write("\n")
    except (PermissionError, OSError, IOError) as e:
        raise OutputWriteError(f"Failed to write output file {path}. Reason: {e}") from e


# Optional CLI entry-point (not required for tests but useful for usage)
def _maybe_parse_cli_and_run():  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Extract TOP N words from text and save as JSON.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-file", dest="input_file", help="Path to input text file.")
    group.add_argument("--input-text", dest="input_text", help="Input text string.")
    parser.add_argument("--output", dest="output", default=str(Path.cwd() / "result.json"), help="Output JSON path.")
    parser.add_argument("--top", dest="top_n", type=int, default=5, help="Number of top words to extract.")

    args = parser.parse_args()

    if args.input_file:
        text = load_text_from_file(args.input_file)
    else:
        text = args.input_text or ""

    try:
        results = analyze_text(text, top_n=args.top_n)
        save_results(results, args.output, top_n=args.top_n)
        print(f"Saved results to {args.output}")
    except EmptyTextError as ete:
        print(f"Error: {ete}")
    except (InputReadError, OutputWriteError) as e:
        print(f"Error: {e}")


if __name__ == ""__main__":  # pragma: no cover
    _maybe_parse_cli_and_run()

