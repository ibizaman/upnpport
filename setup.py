from codecs import open as _open
from os import path

from setuptools import setup

HERE = path.abspath(path.dirname(__file__))
VERSION = '0.1.1'
PACKAGE = 'UPnPPort'

with _open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

    setup(
        name=PACKAGE,
        version=VERSION,
        description='Open ports in',
        long_description=LONG_DESCRIPTION,
        author='Pierre Penninckx',
        author_email='ibizapeanut@gmail.com',
        license='GPLv3',
        packages=[PACKAGE.lower()],
        url='https://github.com/ibizaman/' + PACKAGE.lower(),
        download_url='https://github.com/ibizaman/{}/archive/{}.tar.gz'.format(PACKAGE.lower(), VERSION),
        keywords=['upnp'],
        entry_points = {
            'console_scripts': ['{0}={0}.__main__:main'.format(PACKAGE.lower())],
        },
        install_requires=[
            'PyYAML == 5.1',
        ],
        extras_require={
            'dev': [
                'pylint == 1.7.2',
            ],
            'test': [
                'coverage == 4.4.1',
                'pytest == 3.1.3',
                'pytest-cov == 2.5.1',
            ],
        }
    )
