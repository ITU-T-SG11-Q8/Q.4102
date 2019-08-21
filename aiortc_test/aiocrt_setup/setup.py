
import os.path

import setuptools

install_requires = [
    'aioice>=0.6.13,<0.7.0',
    'attrs',
    'crc32c',
    'cryptography>=2.2',
    'pyee',
    'pylibsrtp>=0.5.6',
    'pyopenssl',
    'websockets'
]

setuptools.setup(
    name='aiortc',
    version='0.5.0',
    packages=['aiortc', 'aiortc.contrib'],
    setup_requires=[],
    install_requires=install_requires,
)
