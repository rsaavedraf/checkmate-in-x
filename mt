#!/bin/bash
(time python3 mateinx.py json-inputs/"game-$1.json" $2 $3) > "sample-outputs/output-game-$1.txt" 2>&1
