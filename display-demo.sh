#!/bin/bash
# SPDX-License-Identifier: MIT

#clear

# Demo to display the changing boards while mateinx
# searches through the games

# game-29: 70.8K games (processed in ~17s recursively,
# but in about 4 mins with the v1.3 iterative implementation)
#time python3 mateinx.py json-inputs/game-29.json -m3 -e -j $1
#time python3 mateinx.py json-inputs/game-29.json -m3 -j $1

# game-21: ~387K games processed in 1m15s
time python3 mateinx.py json-inputs/game-21.json -m3 -g -j $1

# The following takes about 19 mins in same computer,
# number of games evaluated is ~6.13M
#time python3 mateinx.py json-inputs/game-17.json -m5 $1



