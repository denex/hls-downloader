hls-downloader
==============

Download all files as is from HLS (HTTP Live Streaming) VoD (Video on Demand) playlist m3u8 from <https://developer.apple.com/streaming/examples/>

![Python application](https://github.com/denex/hls-downloader/workflows/Python%20application/badge.svg)

Python 2 support
---------------

Branch python2 should work in Python 2

Requirements:

* m3u8
* python-slugify
* requests

Usage:

```sh
python main.py 'http://some.m3u8' /some/dir/for/files/
```

Known Issues:

* No encryption/decryption supported yet
