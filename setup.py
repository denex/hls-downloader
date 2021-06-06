import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hls-downloader",
    version="1.0.1",
    author="Denis Averin",
    author_email="ddenex@gmail.com",
    description="Download all files from HLS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/denex/hls-downloader",
    packages=setuptools.find_packages(),
    classifiers=[],
)
