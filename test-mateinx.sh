#/bin/bash

clear
python3 mateinx.py json-inputs/error-01.json -v -j
python3 mateinx.py json-inputs/error-02.json -v -j
python3 mateinx.py json-inputs/error-03.json -v -j
python3 mateinx.py json-inputs/error-04.json -v -j
python3 mateinx.py json-inputs/error-05.json -v -j -g
python3 mateinx.py json-inputs/error-05.json -v -g -c
python3 mateinx.py json-inputs/error-06.json -v -g
python3 mateinx.py json-inputs/error-07.json -v -g
python3 mateinx.py json-inputs/error-08.json -v
python3 mateinx.py json-inputs/error-09.json -v
python3 mateinx.py json-inputs/error-10.json -v
python3 mateinx.py json-inputs/error-11.json -v
python3 mateinx.py json-inputs/error-12.json -v
python3 mateinx.py json-inputs/game-01.json -m0
python3 mateinx.py json-inputs/game-03.json -j
python3 mateinx.py json-inputs/game-10.json -v -j -m1 -a
python3 mateinx.py json-inputs/game-11.json -v -j -m1 -a
python3 mateinx.py json-inputs/game-12.json -v -j
python3 mateinx.py json-inputs/game-14.json -j -a

# Test problem with more than one 1st move solution
python3 mateinx.py json-inputs/game-16.json -j -a
# Test stopping at 1st find
python3 mateinx.py json-inputs/game-16.json

python3 mateinx.py json-inputs/castles.json -m1 -v -j
python3 mateinx.py json-inputs/game-19.json -j -a

# Here's a mate-in-3, running quite quickly after
# the search trimming optimization
#python3 mateinx.py json-inputs/game-20.json -j -m3

# A moderately difficult mate-in-3:
# takes ~1m 15s exploring ~387K games.
# Solution tree has 602 nodes:
#python3 mateinx.py json-inputs/game-21.json -j -m3

# Quick to find mate-in-4 problems
python3 mateinx.py json-inputs/game-18.json -m4
python3 mateinx.py json-inputs/game-22.json -m4

# Here's a really tough to complete mate-in-5 problem.
# Takes ~19 mins exploring 13.5M games.
# Final solution tree with only one 1st winning move
# has a whopping 190413 nodes
#python3 mateinx.py json-inputs/game-17.json -v -m5

# Test the mate-in-1 which was not being found originally
# (there was a bug with handling in-passing captures, now fixed)
python3 mateinx.py json-inputs/game-25.json -j -v -m2

# Test the iterative implementation (same program
# but with the new option -i)
python3 mateinx.py json-inputs/game-07.json -m2 -a -i
