#!/bin/bash
# Demo to display the boards while mateinx searches
# through 1.1 M games to find a Mate-in-3 solution
# This can take a while (e.g. few minutes) depending
# on your processor
clear
time python3 mateinx.py game-21.json -m3 -g -j -v


