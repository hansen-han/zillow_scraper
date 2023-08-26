from setuptools import setup, find_packages

setup(
    name='ZillowScraper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'bs4>=0.0.1',
        'pandas>=1.1.5',
        # Note: packages in the standard library are not listed here
    ],
    author='Hansen Han',
    author_email='hansenrjhan@gmail.com',
    description='A package for scraping Zillow data'
)