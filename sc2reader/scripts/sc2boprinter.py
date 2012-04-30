#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prints buildorders for all s2gs-files in FOLDER
Usage: python sc2boprinter.py FOLDER
"""

import sys, os, argparse
from sc2reader.factories import SC2Factory

def get(dir):
    factory = SC2Factory()
    
    res = list()
    
    for file in os.listdir(dir):
        if file.rfind('.s2gs') > 0:
            res.append(factory.load_game_summary(os.path.join(dir, file)))
            
    return res
def main():
    parser = argparse.ArgumentParser(description="Prints build orders from all s2gs files in FOLDER")
    parser.add_argument('path', metavar='filename', type=str, nargs=1,
                        help="Path to a folder")

    args = parser.parse_args()
    res = get(args.path[0])
    for r in res:
        if r.__class__.__name__ == "GameSummary":
            print("\n"+"-"*40+"\n")
            print("= {} =".format(r))
            for p in r.players:
                print("== {} - {} ==".format(p.race, p.bnetid if not p.is_ai else "AI"))
                for order in r.build_orders[p.pid]:
                    print("{:0>2}:{:0>2}  {:<35} {:>2}/{}".format(order['time'] / 60,
                                                                  order['time'] % 60,
                                                                  order['order']['name'],
                                                                  order['supply'],
                                                                  order['total_supply']))

if __name__ == '__main__':
    main()
