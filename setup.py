from setuptools import find_packages, setup

setup(
    name="feeds",
    version="2018.7.30",
    # Author details
    author="Florian Preinstorfer, Lukas Anzinger",
    author_email="florian@nblock.org, lukas@lukasanzinger.at",
    url="https://github.com/nblock/feeds",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=6.6",
        "Scrapy>=1.1",
        "bleach>=1.4.3",
        "dateparser>=0.5.1",
        "feedparser",
        "lxml>=3.5.0",
        "python-dateutil>=2.7.3",
        "pyxdg>=0.26",
        "readability-lxml>=0.7",
    ],
    extras_require={
        "docs": ["doc8", "restructuredtext_lint", "sphinx", "sphinx_rtd_theme"],
        "style": ["black", "flake8", "isort"],
    },
    entry_points="""
        [console_scripts]
        feeds=feeds.cli:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Scrapy",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
