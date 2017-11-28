from __future__ import division, print_function

import os
import sys
import argparse
import codecs
import json
import logging
import shutil
from collections import defaultdict

if sys.version_info.major == 2:
    import urlparse  # Python 2.x
else:
    import urllib.parse as urlparse  # Python 3.x

import m3u8

import downloader

DOWNLOADER = None  # Instance of downloader.Downloader

DESCRIPTION = defaultdict(list)


def download_files_from_playlist(m3u8list):
    """
    Get all content from m3u8 playlist
    :type m3u8list: m3u8.M3U8
    :rtype: None
    """
    for media in m3u8list.media:
        if media.absolute_uri:
            DESCRIPTION['MEDIA.' + media.type].append(media.absolute_uri)
            process_playlist_by_uri(media.absolute_uri)

    for iframe_playlist in m3u8list.iframe_playlists:
        if iframe_playlist.absolute_uri:
            DESCRIPTION['IFRAME-STREAMS'].append(iframe_playlist.absolute_uri)
            process_playlist_by_uri(iframe_playlist.absolute_uri)

    if m3u8list.playlists:
        for playlist in m3u8list.playlists:
            if not playlist.absolute_uri.startswith(playlist.base_uri):
                logging.warning("Base URI changed from %s to %s", playlist.base_uri, playlist.absolute_uri)
            process_playlist_by_uri(playlist.absolute_uri)
        return
    assert m3u8list.is_endlist, "Only VOD Playlist supported"
    segment_map_absolute_url = None
    if m3u8list.segment_map:
        segment_map_absolute_url = urlparse.urljoin(m3u8list.base_uri, m3u8list.segment_map['uri'])
    if segment_map_absolute_url:
        DOWNLOADER.download_one_file(segment_map_absolute_url)
    for segment in m3u8list.segments:
        DOWNLOADER.download_one_file(segment.absolute_uri)


def process_playlist_by_uri(absolute_uri):
    """
    Download and process m3u8 playlist
    :type absolute_uri: unicode
    :return: Filename of downloaded Playlist
    :rtype: unicode
    """
    filename = DOWNLOADER.download_one_file(absolute_uri)
    base_uri = '/'.join(absolute_uri.split('/')[:-1]) + '/'

    with codecs.open(filename, mode='rb', encoding='utf-8') as pl_f:
        pl_content = pl_f.read().strip()
    media_playlist = m3u8.M3U8(content=pl_content, base_uri=base_uri)

    download_files_from_playlist(media_playlist)
    return filename


def process_main_playlist(url_to_m3u8):
    """
    Process main playlist and save it to main.m3u8
    Additional information to description.json
    :type url_to_m3u8: unicode
    :rtype: None
    """
    DESCRIPTION['origin_url'] = url_to_m3u8

    main_list_filename = process_playlist_by_uri(url_to_m3u8)

    downloaded_files = DOWNLOADER.downloaded_files_by_url()
    for u in downloaded_files:
        downloaded_files[u] = os.path.relpath(downloaded_files[u], DOWNLOADER.download_dir)
    DESCRIPTION['Files'] = downloaded_files

    main_list_dir = os.path.dirname(main_list_filename)
    description_filename = os.path.join(main_list_dir, 'description.json')
    with codecs.open(description_filename, mode='wb', encoding='utf-8') as jf:
        json.dump(DESCRIPTION, jf, indent=2, separators=(',', ': '))
    logging.info("Description saved to %s", description_filename)

    main_list_copy_filename = os.path.join(main_list_dir, 'main.m3u8')
    if not os.path.isfile(main_list_copy_filename):
        shutil.copy(main_list_filename, main_list_copy_filename)
        logging.info("Copied %s -> %s", main_list_filename, os.path.join(main_list_dir, 'main.m3u8'))


def main(url_to_m3u8, download_dir, verbose):
    """
    :type url_to_m3u8: str 
    :type download_dir: str 
    :type verbose: bool 
    :rtype: None 
    """
    global DOWNLOADER
    DOWNLOADER = downloader.Downloader(download_dir=download_dir)
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    process_main_playlist(url_to_m3u8)


def parse_args():
    """
    :rtype: dict 
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('url_to_m3u8', help="Url to main.m3u8")
    parser.add_argument('download_dir', help="Path to save files")
    parser.add_argument('-v', '--verbose', action="store_true", help="Be more verbose")
    kwargs = vars(parser.parse_args())
    return kwargs


if __name__ == '__main__':
    main(**parse_args())
