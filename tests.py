import os

import pytest

from downloader import Downloader


@pytest.mark.parametrize(
    ("part", "expected"),
    [
        # -.@!
        ("a-b", "a-b"),
        ("a.b", "a.b"),
        ("a@b", "a@b"),
        ("a!b", "a!b"),
        ("a1b", "a1b"),
        # Windows reserved
        ("a<b", "a-b"),
        ("a>b", "a-b"),
        ("a:b", "a-b"),
        ('a"b', "a-b"),
        ("a/b", "a-b"),
        ("a\\b", "a-b"),
        ("a|b", "a-b"),
        ("a?b", "a-b"),
        ("a*b", "a-b"),
    ],
)
def test__filter_filename_part(part, expected):
    assert Downloader.filter_filename_part(part) == expected


@pytest.fixture
def downloader():
    return Downloader(".")


@pytest.mark.parametrize(
    ("url", "expected_filename"), [("http://example.com/seq-427.ts", os.path.join(".", "example.com", "seq-427.ts")),]
)
def test__uri_to_filename(url, expected_filename, downloader):
    assert downloader.uri_to_filename(url) == expected_filename
