import sys
import setuptools

setuptools.setup(
    license="MIT",
    name="sc2reader",
    version="1.7.0",
    keywords=["starcraft 2", "sc2", "replay", "parser"],
    description="Utility for parsing Starcraft II replay files",
    long_description=open("README.rst").read() + "\n\n" + open("CHANGELOG.rst").read(),
    author="Kevin Leung",
    author_email="kkleung89@gmail.com",
    url="https://github.com/ggtracker/sc2reader",
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Real Time Strategy",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "sc2printer = sc2reader.scripts.sc2printer:main",
            "sc2replayer = sc2reader.scripts.sc2replayer:main",
            "sc2parse = sc2reader.scripts.sc2parse:main",
            "sc2attributes = sc2reader.scripts.sc2attributes:main",
            "sc2json = sc2reader.scripts.sc2json:main",
        ]
    },
    install_requires=["mpyq>=0.2.3", "argparse", "ordereddict", "unittest2", "pil"]
    if float(sys.version[:3]) < 2.7
    else ["mpyq>=0.2.4"],
    tests_require=["pytest"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=True,
)
