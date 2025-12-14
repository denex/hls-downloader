import os

import pytest

from downloader import Downloader
from main import HlsDownloaderException, extract_audio_with_ffmpeg, select_audio_input_url

import m3u8


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
        # Windows special dirs see https://docs.microsoft.com/en-gb/windows/win32/fileio/naming-a-file
        # ("CON", "_CON_")
    ],
)
def test__filter_filename_part(part, expected):
    assert Downloader.filter_filename_part(part) == expected


@pytest.fixture
def downloader():
    return Downloader(".")


@pytest.mark.parametrize(
    ("url", "expected_filename"),
    [("http://example.com/seq-427.ts", os.path.join(".", "example.com", "seq-427.ts"))],
)
def test__uri_to_filename(url, expected_filename, downloader):
    assert downloader.uri_to_filename(url) == expected_filename


def test__select_audio_input_url_prefers_audio_rendition():
    content = """#EXTM3U
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"audio\",NAME=\"English\",DEFAULT=YES,AUTOSELECT=YES,URI=\"audio/eng.m3u8\"
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720,AUDIO=\"audio\"
video/high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,AUDIO=\"audio\"
video/low.m3u8
"""
    playlist = m3u8.M3U8(content=content, base_uri="https://example.com/path/")
    selected = select_audio_input_url("https://example.com/path/master.m3u8", playlist)
    assert selected == "https://example.com/path/audio/eng.m3u8"


def test__select_audio_input_url_picks_lowest_bandwidth_variant_when_no_audio_media():
    content = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=3000
high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000
low.m3u8
"""
    playlist = m3u8.M3U8(content=content, base_uri="https://example.com/path/")
    selected = select_audio_input_url("https://example.com/path/master.m3u8", playlist)
    assert selected == "https://example.com/path/low.m3u8"


def test__select_audio_input_url_returns_original_for_media_playlist():
    content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:5
#EXT-X-ENDLIST
"""
    original = "https://example.com/path/media.m3u8"
    playlist = m3u8.M3U8(content=content, base_uri="https://example.com/path/")
    selected = select_audio_input_url(original, playlist)
    assert selected == original


def test__extract_audio_with_ffmpeg_builds_expected_command(monkeypatch, tmp_path):
    calls = {}

    def fake_which(_name):
        return "/usr/bin/ffmpeg"

    def fake_check_call(cmd):
        calls["cmd"] = cmd

    monkeypatch.setattr("main._find_executable", fake_which)
    monkeypatch.setattr("main.subprocess.check_call", fake_check_call)

    out = tmp_path / "out.m4a"
    extract_audio_with_ffmpeg(
        input_url="https://example.com/path/playlist.m3u8",
        output_filename=str(out),
        user_agent="UA",
        ignore_ssl=True,
        overwrite=False,
    )
    cmd = calls["cmd"]
    assert cmd[:1] == ["/usr/bin/ffmpeg"]
    assert "-i" in cmd
    assert "https://example.com/path/playlist.m3u8" in cmd
    assert "-vn" in cmd
    assert ["-c:a", "copy"] == cmd[cmd.index("-c:a") : cmd.index("-c:a") + 2]
    assert ["-user_agent", "UA"] == cmd[cmd.index("-user_agent") : cmd.index("-user_agent") + 2]
    assert ["-tls_verify", "0"] == cmd[cmd.index("-tls_verify") : cmd.index("-tls_verify") + 2]
    assert "-n" in cmd
    assert cmd[-1] == str(out)


def test__extract_audio_with_ffmpeg_requires_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr("main._find_executable", lambda _name: None)
    with pytest.raises(HlsDownloaderException):
        extract_audio_with_ffmpeg(
            input_url="https://example.com/path/playlist.m3u8",
            output_filename=str(tmp_path / "out.m4a"),
        )
