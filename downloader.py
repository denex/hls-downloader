from __future__ import division, print_function

import os
import sys
import logging
from collections import OrderedDict

if sys.version_info.major == 2:
    import urlparse  # Python 2.x
else:
    import urllib.parse as urlparse  # Python 3.x

import requests
import slugify


class Downloader:
    @staticmethod
    def filter_filename_part(string, char_to_replace='_'):
        """
        Replace forbidden filename chars to '_' for string
        :rtype: unicode
        :type string: unicode
        :type char_to_replace: unicode
        """
        result = '.'.join((slugify.slugify(s, separator=char_to_replace) for s in string.split('.')))
        return result

    def __init__(self, download_dir):
        self._download_dir = download_dir
        self._downloaded_files_by_uri = OrderedDict()
        self._http_session = requests.session()
        self._http_headers = {
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/602.4.8 (KHTML, like Gecko)"
                          " Version/10.0.3 Safari/602.4.8"
        }

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
        rel_filename_parts = [url_parts.netloc] + [i for i in url_parts.path.split('/')[1:] if i]
        filtered_parts = [self.filter_filename_part(p) for p in rel_filename_parts]
        rel_filename = os.path.sep.join(filtered_parts)
        filename = os.path.join(self._download_dir, rel_filename)
        return filename

    def url_and_file_size_diff(self, uri, filename):
        """
        Check filename size on server by Content-Length
        :return:
        :type uri: unicode
        :type filename: unicode
        :rtype: int or None
        """
        resp = self._http_session.head(uri, headers=self._http_headers)
        header_size_str = resp.headers.get('Content-Length')
        if header_size_str is None:
            logging.warning("No 'Content-Length' header for %s", uri)
            return None
        uri_size = int(header_size_str)
        file_size = os.path.getsize(filename)
        return uri_size - file_size

    def _retrieve_uri_to_file(self, uri, filename):
        """
        Download URI to File
        :type uri: unicode
        :type filename: unicode
        :rtype: None
        """
        # Downloading
        logging.info("Downloading %s to %s", uri, filename)
        try:
            resp = self._http_session.get(uri, headers=self._http_headers)
        except requests.RequestException as e:
            logging.exception(e)
            raise e
        # Write to file
        with open(filename, 'wb') as fd:
            for chunk in resp.iter_content(chunk_size=2 ** 20):
                fd.write(chunk)

    def download_one_file(self, absolute_uri):
        """
            Downloads one file from absolute_uri to DOWNLOAD_DIR + absolute_uri.path
            if file already exists - skip it
            :type absolute_uri: unicode
            :rtype: unicode
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


def test():
    downloader = Downloader(download_dir=".")
    downloader.download_one_file("http://tungsten.aaplimg.com/VOD/bipbop_adv_example_hevc/master.m3u8")


if __name__ == '__main__':
    test()
