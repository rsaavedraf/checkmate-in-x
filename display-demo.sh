#!/bin/bash
clear

# Demo to display the changing boards while mateinx
# searches through ~387K games to find a Mate-in-3
# solution. Can take a while (e.g. more than 1 min)
# depending on your processor
time python3 mateinx.py json-inputs/game-21.json -m3 -g -j

# The following takes about 19 mins in same computer,
# number of games evaluated is ~6.13M
#time python3 mateinx.py game-17.json -m5


