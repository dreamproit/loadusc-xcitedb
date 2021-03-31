import setuptools

with open("README.adoc", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="loadusc-aih",
    version="0.0.9",
    author="Ari Hershowitz",
    author_email="arihershowitz@gmail.com",
    description="Utilities to scrape and load USC releasepoints into XML database",
    long_description=long_description,
    long_description_content_type="text/asciidoc",
    install_requires=[
        "requests==2.22.0",
        "lxml==4.6.3",
        "beautifulsoup4==4.8.0",
        "pymongo==3.9.0"
    ],
    url="https://github.com/aih/versions/loadusc",
    packages=setuptools.find_packages(),
    package_data={'loadusc': ['data/*.json']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: None",
        "Operating System :: OS Independent",['loadusc.loadusc'],
    ],
)
