from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()

setup(
    name="PyFeeds",
    version="2024.5.1",
    description="DIY Atom feeds in times of social media and paywalls",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Florian Preinstorfer, Lukas Anzinger",
    author_email="florian@nblock.org, lukas@lukasanzinger.at",
    url="https://github.com/PyFeeds/PyFeeds",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "click",
        "dateparser",
        "feedparser",
        "itemloaders",
        "lxml[html_clean]",
        "python-dateutil",
        "pyxdg",
        "readability-lxml",
        "scrapy",
        "scrapy-inline-requests",
    ],
    extras_require={
        "docs": ["sphinx", "sphinx_rtd_theme"],
        "test": ["pytest"],
    },
    entry_points={"console_scripts": ["feeds=feeds.cli:main"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Scrapy",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
