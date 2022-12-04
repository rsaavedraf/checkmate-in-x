#/bin/bash

clear
python3 mateinx.py error-01.json -r -q
python3 mateinx.py error-02.json -r -q
python3 mateinx.py error-03.json -r -q
python3 mateinx.py error-04.json -r -q
python3 mateinx.py error-05.json -r -q
python3 mateinx.py error-05.json -r -q -a
python3 mateinx.py error-06.json -r -q
python3 mateinx.py error-07.json -r -q
python3 mateinx.py error-08.json -r -q
python3 mateinx.py error-09.json -r -q
python3 mateinx.py error-10.json -r -q
python3 mateinx.py error-11.json -r -q
python3 mateinx.py game-01.json -r
python3 mateinx.py game-10.json -r -d1
python3 mateinx.py game-11.json -r -d1
#python3 mateinx.py game-12.json -r -d4
#python3 mateinx.py game-14.json -r -d4
python3 mateinx.py game-16.json -r -d4 -q

# The following can take a few minutes
# (more than 1.1M combinations to explore)
# but it displays nicely
#python3 mateinx.py game-03.json -r -d4
