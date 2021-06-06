from __future__ import division, print_function

import concurrent.futures
import logging
import os
import re
import sys
from collections import OrderedDict
from session import session_factory

import requests
import slugify

if sys.version_info.major == 2:
    import urlparse  # Python 2.x
else:
    import urllib.parse as urlparse  # Python 3.x

import requests

# noinspection PyPackageRequirements
import slugify


class Downloader:
    @staticmethod
    def filter_filename_part(string, allowed_pattern=re.compile(r"[^-.@!\w]+", re.IGNORECASE)):
        """
        Replace forbidden filename chars to '_' for string
        :rtype: Text
        :type string: Text
        :param allowed_pattern:
        """
        result = slugify.slugify(string, lowercase=False, regex_pattern=allowed_pattern)
        return result

    def __init__(self, download_dir, http_settings=None):
        self._download_dir = download_dir
        self._downloaded_files_by_uri = OrderedDict()
        self._http_session = session_factory(http_settings or {})
        self._executor = concurrent.futures.ThreadPoolExecutor()

    @property
    def download_dir(self):
        return self._download_dir

    def downloaded_files_by_url(self):
        return self._downloaded_files_by_uri.copy()

    def uri_to_filename(self, absolute_uri):
        """
        :param absolute_uri:
        :return: DOWNLOAD_DIR + hostname + rel_uri with os.path.sep
        """
        url_parts = urlparse.urlparse(absolute_uri)
        rel_filename_parts = [url_parts.netloc] + [i for i in url_parts.path.split("/")[1:] if i]
        filtered_parts = [self.filter_filename_part(p) for p in rel_filename_parts]
        rel_filename = os.path.sep.join(filtered_parts)
        filename = os.path.join(self._download_dir, rel_filename)
        return filename

    def url_and_file_size_diff(self, uri, filename):
        """
        Check filename size on server by Content-Length
        :return:
        :type uri: Text
        :type filename: Text
        :rtype: int or None
        """
        resp = self._http_session.head(uri)
        header_size_str = resp.headers.get("Content-Length")
        if header_size_str is None:
            logging.warning("No 'Content-Length' header for %s", uri)
            return None
        uri_size = int(header_size_str)
        file_size = os.path.getsize(filename)
        return uri_size - file_size

    def _retrieve_uri_to_file(self, uri, filename):
        """
        Download URI to File
        :type uri: Text
        :type filename: Text
        :rtype: None
        """
        # Downloading
        logging.info("Downloading %s to %s", uri, filename)
        try:
            resp = self._http_session.get(uri)
        except requests.RequestException as e:
            logging.exception(e)
            raise e
        # Write to file
        with open(filename, "wb") as fd:
            for chunk in resp.iter_content(chunk_size=2 ** 20):
                fd.write(chunk)

    def download_one_file(self, absolute_uri):
        """
        Downloads one file from absolute_uri to DOWNLOAD_DIR + absolute_uri.path
        if file already exists - skip it
        :type absolute_uri: Text
        :rtype: Text
        """
        filename = self.uri_to_filename(absolute_uri)
        if filename == self._downloaded_files_by_uri.get(absolute_uri):
            # In case of #EXT-X-BYTERANGE for same file
            logging.warning("File %s already downloaded", filename)
            return filename  # We already downloaded this file in current session
        if os.path.isfile(filename):
            size_diff = self.url_and_file_size_diff(absolute_uri, filename)
            if size_diff == 0:
                self._downloaded_files_by_uri[absolute_uri] = filename
                logging.warning("File %s already exists and same size", filename)
                return filename  # Same file already exists
            if size_diff is not None:  # None means not Content-Length header present
                logging.warning("File %s and URI %s size mismatch", filename, absolute_uri)
        dst_dir = os.path.dirname(filename)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        self._retrieve_uri_to_file(absolute_uri, filename)
        self._downloaded_files_by_uri[absolute_uri] = filename
        logging.info("Downloaded %s -> %s", absolute_uri, filename)
        return filename

    def download_many(self, segments):
        """Downloads many segments and waits for completion"""
        futures = []
        for segment in segments:
            future = self._executor.submit(
                self.download_one_file, segment.absolute_uri)
            futures.append(future)

        for future in futures:
            future.result()


def test():
    downloader = Downloader(download_dir=".")
    downloader.download_one_file("http://tungsten.aaplimg.com/VOD/bipbop_adv_example_hevc/master.m3u8")


if __name__ == "__main__":
    test()
