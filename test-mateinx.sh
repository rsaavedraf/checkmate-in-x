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
python3 mateinx.py game-03.json
python3 mateinx.py game-10.json -v -j -m1
python3 mateinx.py game-11.json -v -j -m1
python3 mateinx.py game-12.json -v -j
python3 mateinx.py game-14.json -j
python3 mateinx.py game-16.json
python3 mateinx.py castles.json -v -j
python3 mateinx.py game-19.json -j

# Here's a mate-in-3, running quite quickly after
# the search trimming optimization
python3 mateinx.py game-20.json -j -m3

