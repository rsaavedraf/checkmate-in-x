#/bin/bash

clear
python3 mateinx.py error-01.json -v -j
python3 mateinx.py error-02.json -v -j
python3 mateinx.py error-03.json -v -j
python3 mateinx.py error-04.json -v -j
python3 mateinx.py error-05.json -v -j -g
python3 mateinx.py error-05.json -v -g -a
python3 mateinx.py error-06.json -v -g
python3 mateinx.py error-07.json -v -g
python3 mateinx.py error-08.json -v
python3 mateinx.py error-09.json -v
python3 mateinx.py error-10.json -v
python3 mateinx.py error-11.json -v
python3 mateinx.py game-01.json -m0
python3 mateinx.py game-03.json -j
python3 mateinx.py game-10.json -v -j -m1
python3 mateinx.py game-11.json -v -j -m1
python3 mateinx.py game-12.json -v -j
python3 mateinx.py game-14.json -j
python3 mateinx.py game-16.json -j
python3 mateinx.py castles.json -v -j
python3 mateinx.py game-19.json -j

# Here's a mate-in-3, running quite quickly after
# the search trimming optimization
python3 mateinx.py game-20.json -j -m3

# A moderately difficult mate-in-3:
# takes about 3.3 mins exploring 1.1M games,
# solution has 602 nodes, only one 1st winning move
#python3 mateinx.py game-21.json -j -m3

# Quick to find mate-in-4 problems
python3 mateinx.py game-18.json -v -m4
python3 mateinx.py game-22.json -v -m4

# Here's a really tough to complete mate-in-5 problem.
# Takes almost 40 mins exploring 13.5M games.
# final solution tree with only one 1st winning move
# has a whopping 190413 nodes
#python3 mateinx.py game-17.json -v -m5
