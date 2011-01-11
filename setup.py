from setuptools import setup, find_packages

setup(
	name="sc2reader",
	version="0.1.0",
	license="MIT",
	
	author="Graylin Kim",
	author_email="graylin.kim@gmail.com",
	url="https://github.com/GraylinKim/sc2reader",
	
	description="Utility for parsing Starcraft II replay files",
	long_description=''.join(open("README.txt").readlines()),
	keywords=["starcraft 2","sc2","parser","replay"],
	classifiers=[
			"Environment :: Console",
			"Development Status :: 4 - Beta",
			"Programming Language :: Python",
			"Programming Language :: Python 2.7",
			"Intended Audience :: Developers",
			"License :: OSI Approved :: MIT License",
			"Natural Language :: English",
			"Operating System :: OS Independent",
			"Environment :: Other Environment",
			"Topic :: Utilities",
			"Topic :: Software Development :: Libraries",
			"Topic :: Games/Entertainment :: Real Time Strategy",
		],
	
	requires=['mpyq'],
    install_requires=['mpyq'],
	packages=['sc2reader'],
	scripts=['scripts/sc2printer'],
)