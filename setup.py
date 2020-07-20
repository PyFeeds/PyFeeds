from setuptools import find_packages, setup

with open("README.rst") as f:
    long_description = f.read()

setup(
    name="PyFeeds",
    version="2020.5.16",
    description="DIY Atom feeds in times of social media and paywalls",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Florian Preinstorfer, Lukas Anzinger",
    author_email="florian@nblock.org, lukas@lukasanzinger.at",
    url="https://github.com/PyFeeds/PyFeeds",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "Click>=6.6",
        "Scrapy>=2.2",
        "bleach>=1.4.3",
        "dateparser>=0.5.1",
        "feedparser",
        "lxml>=3.5.0",
        "python-dateutil>=2.7.3",
        "pyxdg>=0.26",
        "readability-lxml>=0.7",
        "scrapy-inline-requests",
        "itemloaders",  # explicit dependency of Scrapy > 2.2.1
    ],
    extras_require={
        "docs": ["sphinx", "sphinx_rtd_theme"],
        "style": [
            "black",
            "doc8",
            "flake8",
            "isort>=5",
            "pygments",
            "restructuredtext_lint",
        ],
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
