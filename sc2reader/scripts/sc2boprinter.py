#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prints buildorders for all s2gs-files in FOLDER
Usage: python sc2boprinter.py FOLDER
"""

import sys, os
from sc2reader.factories import SC2Factory

def get():
    factory = SC2Factory()
    
    res = list()
    
    for file in os.listdir(sys.argv[1]):
        if file.rfind('.s2gs') > 0:
            res.append(factory.load_game_summary(sys.argv[1] + "\\" + file))
        elif file.rfind('.s2mi') > 0:
            res.append(factory.load_map_info(sys.argv[1] + "\\" + file))
        elif file.rfind('.s2mh') > 0:
            res.append(factory.load_map_header(sys.argv[1] + "\\" + file))
    
    return res

res = get()
for r in res:
    if r.__class__.__name__ == "GameSummary":
        print("= {} =".format(r))
        for p in r.players:
            print("== {} - {} ==".format(p.race, p.bnetid if not p.is_ai else "AI"))
            for order in r.build_orders[p.pid]:
                print("{:0>2}:{:0>2}  {:<35} {:>2}/{}".format(order['time'] / 60,
                                                              order['time'] % 60,
                                                              order['order']['name'],
                                                              order['supply'],
                                                              order['total_supply']))
