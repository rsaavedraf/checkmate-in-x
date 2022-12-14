# checkmate-in-x
A coding challenge: Checkmate-in-X finder, first in python, then Rust.
By Raul Saavedra F, Nov-2022

A mate-in-x finding program not only is a relatively demanding coding
challenge on its own. I think a multithreaded implementation of it can
offer a great immersion opportunity into Rust.

Problem statement: given a starting chess board game setup (e.g.
readable from a .json file,) find out all mate-in-X combination of
moves for the player that moves first.

The implementation should exhaustively brute-force its way through
absolutely all valid combination of moves down to a maximum specified depth,
to find out all possible outcomes of the game (wins or draws) till there.
From that exploration, it must identify (if there are any) the desirable
mate-in-X sequence of moves for the starting player.

The plan is to first write a single-threaded python version, making sure
the chess game and moves are correctly and completely modelled (e.g.
including also castle moves, pawn promotions, etc.) also making sure 
the correct mate-in-X solution(s) is/are found, of course.

Once the python version is done as baseline/point of reference,
the idea is to then write two functionally equivalent implementations
in the Rust language: one single-threaded, then another multi-threaded.
Then finally compare their performance, i.e. fill out a table like the
following with their (relative?) execution times for specific Mate-in-X
problems, all running on the same machine:


|  To find   | Python | Rust-ST | Rust-MT (ie. 4 cores) |
|:-----------|:------:|:-------:|:-------:|
| Mate-in-2a | x1     | y1      | z1      |
| Mate-in-2b | x2     | y2      | z2      |
| ....       |        |         |         |
| Mate-in-3a | ...    | ...     | ...     |
| Mate-in-3b |        |         |         |
| ....       |        |         |         |

## Update 2022-12-08:
* Support castle moves done!
* Major simple optimization added: no need to explore any additional moves
for the 'losing' player as soon as we find that one of his possible moves
guarantees survival within the x number of moves of interest.
This simple check trims down the search space massively, in fact by
orders of magnitude.

## Update 2022-12-09:
Minor changes in the outputs, after realizing how huge the output tree of
moves can get (i.e. for game-17.json a single 1st move can achieve the
mate-in-5, but the final tree of moves has a whopping 190413 nodes
in total)

## Update 2022-12-13
Usage/help for the script added.
Calling this version v1.0 proper, pretty much finished for the required 
functionality.

## Update 2022-12-14
v1.1 after a bug found and fixed: when a pawn was getting captured in passing,
it was not getting properly removed from the board and remaining pieces. 
Also such capturing move was missing the "x" when printed out.

## Update 2022-12-15
v1.1.1 after another bug found and fixed: when exploring the possibility 
of in-passing capture, if the last move was unknown (None) the program 
was crashing checking for last move being () (older representation)
instead of None. 
game-10.json modified to test this case and make sure it runs problem-free.

## Update 2022-12-17
v1.2 with a first iterative implementation (runs using option -i, so
not a separate program). Runs well but not yet finished, since it still
does not have the quite significant trimming speed-up that the recursive
one does.

## Update 2022-12-18
v.1.3 modified iterative implementation now made depth-first (imitating
recursive one), and also now including the "speed-up" trimming.
However at least for now it is massively slower than the recursive one
(~14x the time)

## Update 2022-12-29
v.1.4 debugged and fixed iterative implementation, now goes through
exactly the same sequence of games and search trims done by the recursive
one. Iterative still slightly slower (5-7% more time), but now in the
same ballpark as the recursive.

## Next tasks:
- Implement a single threaded Rust version
- Implement a multithreaded Rust version
