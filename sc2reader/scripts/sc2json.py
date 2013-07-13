#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import sc2reader
from sc2reader.plugins.replay import toJSON

def main():
    factory = sc2reader.factories.SC2Factory()
    factory.register_plugin("Replay", toJSON())

    replay_json = factory.load_replay(sys.argv[1])
    print replay_json

if __name__ == '__main__':
    main()
