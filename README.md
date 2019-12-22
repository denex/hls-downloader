# hls-downloader

Download all files as is from HLS (HTTP Live Streaming) VoD (Video on Demand) playlist m3u8 from <https://developer.apple.com/streaming/examples/>

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
