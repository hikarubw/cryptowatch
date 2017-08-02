from setuptools import setup, find_packages

setup(
    name='cryptowatch',
    version='0.0.1',
    description='cryptowatch api wrapper',
    long_description='https://pypi.python.org/pypi/cryptowatch',
    url='https://github.com/Akira-Taniguchi/cryptowatch',
    author='AkiraTaniguchi',
    author_email ='dededededaiou2003@yahoo.co.jp',
    packages=find_packages(),
    license='MIT',
    keywords='api cryptowatch ohlc',
    install_requires=['requests==2.18.2']
)