import io
import sys
from pathlib import Path

from convert import convert


def test_convertion():
    input = (Path(__file__).parent / "test_input.txt").read_text()
    expected = (Path(__file__).parent / "test_expected.csv").read_text()

    buf = io.StringIO()
    convert(buf, input, 2019, "123.22", "89466.05")

    result = buf.getvalue()
    assert result == expected
