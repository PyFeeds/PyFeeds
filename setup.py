from setuptools import setup, find_packages

setup(
    name='feeds',
    version='0.1-dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click>=6.6',
        'Jinja2>=2.8',
        'Scrapy>=1.1.0rc3',
        'pytz>=2016.4',
        'lxml>=3.5.0',
    ],
    entry_points='''
        [console_scripts]
        feeds=feeds.cli:main
    ''',
)
