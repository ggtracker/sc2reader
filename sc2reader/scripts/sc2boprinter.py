#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prints buildorders for all s2gs-files in FOLDER
Usage: python sc2boprinter.py FOLDER
"""

import sys, os, argparse, sc2reader

def main():
    parser = argparse.ArgumentParser(description="Prints build orders from all s2gs files in FOLDER")
    parser.add_argument('path', metavar='filename', type=str, nargs=1, help="Path to a folder")
    args = parser.parse_args()
    for r in sc2reader.load_game_summaries(args.path):
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
