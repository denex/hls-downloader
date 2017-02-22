from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import codecs
import json
import logging
import os
import shutil
import urlparse
from collections import OrderedDict, defaultdict

import m3u8
import requests


DOWNLOAD_DIR = None

DESCRIPTION = defaultdict(list)

FILENAME_CHARS_TO_REPLACE = frozenset(['<', '>', ':', '"', '|', '?', '*', '/', '\\'])


def filter_filename_part(string, char_to_replace='_'):
    """
    Replace forbidden filename chars to '_' for string
    :rtype: unicode
    :type string: unicode
    :type char_to_replace: unicode
    """
    f_part = [(c if c not in FILENAME_CHARS_TO_REPLACE else char_to_replace) for c in string]
    return ''.join(f_part)


def uri_to_filename(absolute_uri):
    """
    :param absolute_uri:
    :return: DOWNLOAD_DIR + hostname + rel_uri with os.path.sep
    """
    url_parts = urlparse.urlparse(absolute_uri)
    rel_filename_parts = [url_parts.netloc] + filter(lambda s: s != '', url_parts.path.split('/')[1:])
    filtered_parts = [filter_filename_part(p) for p in rel_filename_parts]
    rel_filename = os.path.sep.join(filtered_parts)
    filename = os.path.join(DOWNLOAD_DIR, rel_filename)
    return filename


Headers = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8"
}

HTTP_SESSION = requests.session()


def is_file_same_size(uri, filename):
    """
    Check server size by Content-Length
    :type uri: unicode
    :type filename: unicode
    :rtype: bool
    """
    resp = HTTP_SESSION.head(uri, headers=Headers)
    header_size_str = resp.headers.get('Content-Length')
    if header_size_str is None:
        logging.warning("No 'Content-Length' header for %s", uri)
        return False
    uri_size = int(header_size_str)

    file_size = os.path.getsize(filename)
    return (uri_size - file_size) == 0


def retrieve_uri_to_file(uri, filename):
    """
    Download URI to File
    :type uri: unicode
    :type filename: unicode
    :rtype: None
    """
    # Downloading
    try:
        resp = HTTP_SESSION.get(uri, headers=Headers)
    except requests.RequestException as e:
        logging.exception(e)
        raise e
    # Write to file
    with open(filename, 'wb') as fd:
        for chunk in resp.iter_content(chunk_size=2 ** 20):
            fd.write(chunk)


DOWNLOADED_FILES_BY_URI = OrderedDict()


def download_one_file(absolute_uri):
    """
    Downloads one file from absolute_uri to DOWNLOAD_DIR + absolute_uri.path
    if file already exists - skip it
    :type absolute_uri: unicode
    :rtype: unicode
    """
    filename = uri_to_filename(absolute_uri)
    if filename == DOWNLOADED_FILES_BY_URI.get(absolute_uri):
        # In case of #EXT-X-BYTERANGE for same file
        logging.warning("File %s already downloaded", filename)
        return filename  # We already downloaded this file in current session
    if os.path.isfile(filename):
        if is_file_same_size(absolute_uri, filename):
            DOWNLOADED_FILES_BY_URI[absolute_uri] = filename
            logging.warning("File %s already exists and same size", filename)
            return filename  # Same file already exists
        logging.warning("File %s and URI %s size mismatch", filename, absolute_uri)
    dst_dir = os.path.dirname(filename)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    retrieve_uri_to_file(absolute_uri, filename)
    DOWNLOADED_FILES_BY_URI[absolute_uri] = filename
    logging.info("Downloaded %s -> %s", absolute_uri, filename)
    return filename


def download_files_from_playlist(m3u8list):
    """
    Get all content from m3u8 playlist
    :type m3u8list: m3u8.M3U8
    :rtype: None
    """
    for iframe_playlist in m3u8list.iframe_playlists:
        if iframe_playlist.absolute_uri:
            DESCRIPTION['IFRAME-STREAMS'].append(iframe_playlist.absolute_uri)
            process_playlist_by_uri(iframe_playlist.absolute_uri)

    for media in m3u8list.media:
        if media.absolute_uri:
            DESCRIPTION['MEDIA.' + media.type].append(media.absolute_uri)
            process_playlist_by_uri(media.absolute_uri)

    if m3u8list.playlists:
        for playlist in m3u8list.playlists:
            process_playlist_by_uri(playlist.absolute_uri)
        return
    assert m3u8list.is_endlist, "Only VOD Playlist supported"
    for segment in m3u8list.segments:
        download_one_file(segment.absolute_uri)


def process_playlist_by_uri(absolute_uri):
    """
    Download and process m3u8 playlist
    :type absolute_uri: unicode
    :return: Filename of downloaded Playlist
    :rtype: unicode
    """
    filename = download_one_file(absolute_uri)
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

    for u in DOWNLOADED_FILES_BY_URI:
        DOWNLOADED_FILES_BY_URI[u] = os.path.relpath(DOWNLOADED_FILES_BY_URI[u], DOWNLOAD_DIR)
    DESCRIPTION['Files'] = DOWNLOADED_FILES_BY_URI

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
    global DOWNLOAD_DIR
    DOWNLOAD_DIR = download_dir
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    process_main_playlist(url_to_m3u8)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url_to_m3u8', help="Url to main.m3u8")
    parser.add_argument('download_dir', help="Path to save files")
    parser.add_argument('-v', '--verbose', action="store_true", help="Be more verbose")
    kwargs = vars(parser.parse_args())
    return kwargs


if __name__ == '__main__':
    main(**parse_args())
