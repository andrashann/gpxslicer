import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="gpxslicer",
    version="0.1.0",
    description="Slice up gpx tracks based on distance from the start or custom waypoints",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/andrashann/gpxslicer",
    author="András Hann",
    author_email="dev@hann.io",
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Utilities"
    ],
    packages=["gpxslicer"],
    install_requires=["gpxpy"],
    entry_points={
        "console_scripts": [
            "gpxslicer=gpxslicer.__main__:main",
        ]
    },
)