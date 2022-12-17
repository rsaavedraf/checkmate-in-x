#!/bin/bash
clear

# Demo to display the changing boards while mateinx
# searches through the games

# game-29: 70.8K games processed in ~17s
time python3 mateinx.py json-inputs/game-29.json -m3 -g -j

# game-21: ~387K games processed in 1m15s
#time python3 mateinx.py json-inputs/game-21.json -m3 -g -j

# The following takes about 19 mins in same computer,
# number of games evaluated is ~6.13M
#time python3 mateinx.py game-17.json -m5



