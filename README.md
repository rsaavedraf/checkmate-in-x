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

## Update 2022-12-04:
The python script is working well and almost done now.
Only pending tasks for it:
- Support castle moves
- Write up usage/help for the it
- Change recursive scheme to iterative (this will likely be convenient for a multithreaded rewrite)

