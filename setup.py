import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'dash',
    'dash-bootstrap-components',
    'pydicom',
    'PyPubSub',
    'watchdog',
    'numpy',
    'sortedcontainers',
    'plotly',
    'pandas',
    'retry',
    'redis',
    'pyyaml'
]

about = dict()
with open(os.path.join(here, 'rtbold', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=find_packages(),
    package_data={
        '': ['*.yaml', '*.tcss', '*.mp3']
    },
    include_package_data=True,
    scripts=[
        'scripts/start.py',
        'scripts/simulator.py'
    ],
    install_requires=requires
)
