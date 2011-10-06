import setuptools, sys
from sc2reader import __version__ as version

setuptools.setup(
	name="sc2reader",
	version=version,
	license="MIT",
	
	author="Graylin Kim",
	author_email="graylin.kim@gmail.com",
	url="https://github.com/GraylinKim/sc2reader",
	
	description="Utility for parsing Starcraft II replay files",
	long_description=open("README.txt").read(),
	keywords=["starcraft 2","sc2","parser","replay"],
	classifiers=[
			"Environment :: Console",
			"Development Status :: 4 - Beta",
			"Programming Language :: Python",
			"Programming Language :: Python :: 2.7",
			"Intended Audience :: Developers",
			"License :: OSI Approved :: MIT License",
			"Natural Language :: English",
			"Operating System :: OS Independent",
			"Environment :: Other Environment",
			"Topic :: Utilities",
			"Topic :: Software Development :: Libraries",
			"Topic :: Games/Entertainment :: Real Time Strategy",
		],
	entry_points={
        'console_scripts': [
            'sc2autosave = sc2reader.scripts.sc2autosave:main',
            'sc2printer = sc2reader.scripts.sc2printer:main',
            'sc2store = sc2reader.scripts.sc2store:main',
        ]
    },
	install_requires=['mpyq','argparse'] if float(sys.version[:3]) < 2.7 else ['mpyq'],
	packages=['sc2reader', 'sc2reader.scripts', 'sc2reader.processors'],
)
