#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import sc2reader

def main():
	for replay in sc2reader.load_replays(sys.argv[1:], verbose=True):
		pass

if __name__ == '__main__':
    main()