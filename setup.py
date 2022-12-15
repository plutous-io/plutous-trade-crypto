import setuptools
from plutous.trade.crypto import __version__


setuptools.setup(
    name="plutous-trade-crypto",
    packages=setuptools.find_packages(),
    include_package_data=True,
    version=__version__,
    python_requires=">=3.10.*",
    description="Plutous Crypto Trading Library",
    author="Plutous",
    author_email="cheunhong@plutous.io",
    url="https://github.com/plutous-io/plutous-trade-crypto",
    install_requires=[
        "ccxt",
    ],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
