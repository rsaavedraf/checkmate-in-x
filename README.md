# checkmate-in-x
A coding challenge: Checkmate-in-X finder, first in python, then... some other
language. (Because of recent trademarking moves done by the Rust Foundation,
withholding the idea of rewriting in Rust for now.)
By Raul Saavedra F, Nov-2022

A mate-in-x finding program not only is a relatively demanding coding
challenge on its own. I think a multithreaded implementation of it can
offer a great immersion opportunity into any programming language.

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

Once the single-threaded python version is done as baseline/point of reference, 
the idea is to then write a multi-threaded version, and then two functionally 
equivalent implementations in another, faster language: one single-threaded, then 
another multi-threaded. Then finally compare their performance, i.e. fill out a 
table like the following with their (relative?) execution times for specific 
Mate-in-X problems, all running on the same machine:


|  To find   | Python | Python-MT | Another lang. | Another lang.-MT |
|:-----------|:------:|:---------:|:----:|:-------:|
| Mate-in-2a | x1     | xm1       | y1   | ym1     |
| Mate-in-2b | x2     | xm2       | y2   | ym2     |
| ...        | | | | |
| Mate-in-3a | ... | ... | ... | ... |
| Mate-in-3b | | | | |
| ...        | | | | |

## Next tasks:
- Implement a multithreaded Python version
- Implement a single threaded version in another language
- Implement a multithreaded version in that language

File last_updates.txt in the repository has a list of important milestones reached 
during the development.
