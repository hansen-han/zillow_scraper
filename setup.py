from setuptools import setup, find_packages

setup(
    name='zillow_scraper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'bs4>=0.0.1',
        'pandas>=1.1.5',
    ],
    author='Hansen Han',
    author_email='hansenrjhan@gmail.com',
    description='A package for scraping Zillow data'
)