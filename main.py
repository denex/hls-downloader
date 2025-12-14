#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import codecs
import json
import logging
import os
import subprocess
import shutil
import sys
from collections import defaultdict

if sys.version_info.major == 2:
    import urlparse  # Python 2.x
else:
    import urllib.parse as urlparse  # Python 3.x

import m3u8

import downloader


class HlsDownloaderException(Exception):
    pass


DOWNLOADER = None  # Instance of downloader.Downloader

DESCRIPTION = defaultdict(list)

if sys.version_info.major == 2:
    from distutils.spawn import find_executable as _find_executable  # Python 2.x
else:
    from shutil import which as _find_executable  # Python 3.x


def download_files_from_playlist(m3u8list):
    """
    Get all content from m3u8 playlist
    :type m3u8list: m3u8.M3U8
    :rtype: None
    """
    for media in m3u8list.media:
        if media.absolute_uri:
            DESCRIPTION["MEDIA." + media.type].append(media.absolute_uri)
            process_playlist_by_uri(media.absolute_uri)

    for iframe_playlist in m3u8list.iframe_playlists:
        if iframe_playlist.absolute_uri:
            DESCRIPTION["IFRAME-STREAMS"].append(iframe_playlist.absolute_uri)
            process_playlist_by_uri(iframe_playlist.absolute_uri)

    if m3u8list.playlists:
        for playlist in m3u8list.playlists:
            if not playlist.absolute_uri.startswith(playlist.base_uri):
                logging.warning(
                    "Base URI changed from %s to %s",
                    playlist.base_uri,
                    playlist.absolute_uri,
                )
            process_playlist_by_uri(playlist.absolute_uri)
        return

    # noinspection PyUnresolvedReferences
    if not m3u8list.is_endlist:
        raise HlsDownloaderException("Playlist is not endlist. Only VOD Playlists are supported")

    segment_map_absolute_url = None
    if m3u8list.segment_map:
        segment_map_absolute_url = urlparse.urljoin(m3u8list.base_uri, m3u8list.segment_map[0].uri)
    if segment_map_absolute_url:
        DOWNLOADER.download_one_file(segment_map_absolute_url)

    DOWNLOADER.download_many(m3u8list.segments)


def load_playlist_by_uri(absolute_uri):
    """
    Download and parse m3u8 playlist.
    :type absolute_uri: Text
    :return: (local filename, parsed playlist)
    :rtype: (Text, m3u8.M3U8)
    """
    filename = DOWNLOADER.download_one_file(absolute_uri)
    base_uri = "/".join(absolute_uri.split("/")[:-1]) + "/"

    with codecs.open(filename, mode="rb", encoding="utf-8") as pl_f:
        pl_content = pl_f.read().strip()
    media_playlist = m3u8.M3U8(content=pl_content, base_uri=base_uri)
    return filename, media_playlist


def process_playlist_by_uri(absolute_uri):
    """
    Download and process m3u8 playlist
    :type absolute_uri: Text
    :return: Filename of downloaded Playlist
    :rtype: Text
    """
    filename, media_playlist = load_playlist_by_uri(absolute_uri)
    download_files_from_playlist(media_playlist)
    return filename


def select_audio_input_url(original_url, playlist, prefer_lowest_bandwidth=True):
    """
    Pick a playlist URL suitable for extracting audio.

    Prefer an AUDIO rendition if present; otherwise choose a variant playlist
    by bandwidth (lowest by default) to reduce unnecessary video download.

    :type original_url: Text
    :type playlist: m3u8.M3U8
    :type prefer_lowest_bandwidth: bool
    :rtype: Text
    """
    audio_media = []
    for media in getattr(playlist, "media", []) or []:
        if getattr(media, "type", "").upper() != "AUDIO":
            continue
        if not getattr(media, "absolute_uri", None):
            continue
        audio_media.append(media)

    if audio_media:
        for candidate in audio_media:
            if getattr(candidate, "default", False):
                return candidate.absolute_uri
        for candidate in audio_media:
            if getattr(candidate, "autoselect", False):
                return candidate.absolute_uri
        return audio_media[0].absolute_uri

    playlists = getattr(playlist, "playlists", None) or []
    if not playlists:
        return original_url

    def playlist_bandwidth(item):
        stream_info = getattr(item, "stream_info", None)
        bandwidth = getattr(stream_info, "bandwidth", None)
        if bandwidth is None:
            return float("inf") if prefer_lowest_bandwidth else float("-inf")
        return bandwidth

    selected = sorted(playlists, key=playlist_bandwidth, reverse=not prefer_lowest_bandwidth)[0]
    if getattr(selected, "absolute_uri", None):
        return selected.absolute_uri
    return original_url


def extract_audio_with_ffmpeg(input_url, output_filename, user_agent=None, ignore_ssl=False, overwrite=False):
    """
    Extract audio track from an HLS URL into a single file using ffmpeg.
    :type input_url: Text
    :type output_filename: Text
    :type user_agent: Text or None
    :type ignore_ssl: bool
    :type overwrite: bool
    :rtype: None
    """
    ffmpeg_path = _find_executable("ffmpeg")
    if not ffmpeg_path:
        raise HlsDownloaderException(
            "ffmpeg not found in PATH. Install ffmpeg or run without --audio-only.",
        )

    out_dir = os.path.dirname(output_filename)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y" if overwrite else "-n",
    ]
    if user_agent:
        cmd += ["-user_agent", user_agent]
    if ignore_ssl:
        cmd += ["-tls_verify", "0"]
    cmd += [
        "-i",
        input_url,
        "-vn",
        "-sn",
        "-dn",
        "-map",
        "0:a:0",
        "-c:a",
        "copy",
        output_filename,
    ]

    logging.info("Running: %s", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except (OSError, subprocess.CalledProcessError) as e:
        raise HlsDownloaderException("ffmpeg failed to extract audio: %s" % e)


def process_main_playlist(url_to_m3u8):
    """
    Process main playlist and save it to main.m3u8
    Additional information to description.json
    :type url_to_m3u8: Text
    :rtype: None
    """
    DESCRIPTION["origin_url"] = url_to_m3u8

    main_list_filename = process_playlist_by_uri(url_to_m3u8)

    downloaded_files = DOWNLOADER.downloaded_files_by_url()
    for u in downloaded_files:
        downloaded_files[u] = os.path.relpath(downloaded_files[u], DOWNLOADER.download_dir)
    DESCRIPTION["Files"] = downloaded_files

    main_list_dir = os.path.dirname(main_list_filename)
    description_filename = os.path.join(main_list_dir, "description.json")
    with codecs.open(description_filename, mode="wb", encoding="utf-8") as jf:
        json.dump(DESCRIPTION, jf, indent=2, separators=(",", ": "))
    logging.info("Description saved to %s", description_filename)

    main_list_copy_filename = os.path.join(main_list_dir, "main.m3u8")
    if not os.path.isfile(main_list_copy_filename):
        shutil.copy(main_list_filename, main_list_copy_filename)
        logging.info(
            "Copied %s -> %s",
            main_list_filename,
            os.path.join(main_list_dir, "main.m3u8"),
        )


def process_audio_only(url_to_m3u8, ignore_ssl, user_agent, audio_out=None, overwrite=False):
    """
    Download audio track only (best-effort) and save it next to downloaded playlist.
    :type url_to_m3u8: str
    :type ignore_ssl: bool
    :type user_agent: str
    :type audio_out: str or None
    :type overwrite: bool
    :rtype: None
    """
    DESCRIPTION["origin_url"] = url_to_m3u8
    DESCRIPTION["audio_only"] = True

    main_list_filename, main_playlist = load_playlist_by_uri(url_to_m3u8)
    main_list_dir = os.path.dirname(main_list_filename)

    audio_input_url = select_audio_input_url(
        original_url=url_to_m3u8,
        playlist=main_playlist,
        prefer_lowest_bandwidth=True,
    )
    DESCRIPTION["audio_input_url"] = audio_input_url

    # Save a copy of the top-level playlist for reference (mirrors process_main_playlist()).
    main_list_copy_filename = os.path.join(main_list_dir, "main.m3u8")
    if not os.path.isfile(main_list_copy_filename):
        shutil.copy(main_list_filename, main_list_copy_filename)

    # Also download the selected input playlist so the output directory contains all relevant manifests.
    if audio_input_url != url_to_m3u8:
        DOWNLOADER.download_one_file(audio_input_url)

    if audio_out is None:
        audio_out = os.path.join(main_list_dir, "audio.m4a")
    DESCRIPTION["audio_output"] = os.path.relpath(audio_out, main_list_dir)

    extract_audio_with_ffmpeg(
        input_url=audio_input_url,
        output_filename=audio_out,
        user_agent=user_agent,
        ignore_ssl=ignore_ssl,
        overwrite=overwrite,
    )
    logging.info("Audio saved to %s", audio_out)

    downloaded_files = DOWNLOADER.downloaded_files_by_url()
    for u in downloaded_files:
        downloaded_files[u] = os.path.relpath(downloaded_files[u], DOWNLOADER.download_dir)
    DESCRIPTION["Files"] = downloaded_files

    description_filename = os.path.join(main_list_dir, "description.json")
    with codecs.open(description_filename, mode="wb", encoding="utf-8") as jf:
        json.dump(DESCRIPTION, jf, indent=2, separators=(",", ": "))
    logging.info("Description saved to %s", description_filename)


def main(url_to_m3u8, download_dir, verbose, ignore_ssl, audio_only=False, audio_out=None, overwrite=False):
    """
    :type url_to_m3u8: str
    :type download_dir: str
    :type verbose: bool
    :type ignore_ssl: bool
    :type audio_only: bool
    :type audio_out: str or None
    :type overwrite: bool
    :rtype: None
    """
    http_settings = dict(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)"
            " AppleWebKit/602.4.8 (KHTML, like Gecko)"
            " Version/10.0.3 Safari/602.4.8"
        },
    )
    if ignore_ssl:
        http_settings["verify"] = False

    global DOWNLOADER
    DOWNLOADER = downloader.Downloader(
        download_dir=download_dir,
        http_settings=http_settings,
    )
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    if audio_only:
        process_audio_only(
            url_to_m3u8=url_to_m3u8,
            ignore_ssl=ignore_ssl,
            user_agent=http_settings.get("headers", {}).get("User-Agent"),
            audio_out=audio_out,
            overwrite=overwrite,
        )
    else:
        process_main_playlist(url_to_m3u8)


def parse_args():
    """
    :rtype: dict
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("url_to_m3u8", help="Url to main.m3u8")
    parser.add_argument("download_dir", help="Path to save files")
    parser.add_argument(
        "--ignore-ssl",
        default=False,
        action="store_true",
        help="Ignore SSL verification",
    )
    parser.add_argument(
        "--audio-only",
        default=False,
        action="store_true",
        help="Extract and save audio track only (requires ffmpeg)",
    )
    parser.add_argument(
        "--audio-out",
        default=None,
        help="Path for audio output file (default: <downloaded playlist dir>/audio.m4a)",
    )
    parser.add_argument(
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite existing output files (audio-only mode)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Be more verbose")
    kwargs = vars(parser.parse_args())
    return kwargs


def module_entry_point():
    main(**parse_args())


if __name__ == "__main__":
    module_entry_point()
