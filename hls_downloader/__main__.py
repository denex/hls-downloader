from __future__ import division, print_function

import argparse
import logging

from . import downloader, main


def module_entry_point(url_to_m3u8, download_dir, verbose):
    """
    :type url_to_m3u8: str
    :type download_dir: str
    :type verbose: bool
    :rtype: None
    """
    main.DOWNLOADER = downloader.Downloader(download_dir=download_dir)
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    main.process_main_playlist(url_to_m3u8)


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
    module_entry_point(**parse_args())
