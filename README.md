hls-downloader
==============

Download all files as is from HLS (HTTP Live Streaming) VoD (Video on Demand) playlist m3u8 from <https://developer.apple.com/streaming/examples/>

![Python application](https://github.com/denex/hls-downloader/workflows/Python%20application/badge.svg)

Python 2 suport
---------------

Branch python2 should work in Python 2

## Install

Project dependencies are managed with [uv](https://docs.astral.sh/uv/). Create a virtual environment with the dev tooling by running:

```sh
uv sync --group dev
```

Usage:

```sh
uv run python main.py 'http://some.m3u8' /some/dir/for/files/
```

Known Issues:

* No encryption/decryption supported yet
