#!/usr/bin/env python
# SPDX-License-Identifier: MIT

"""
mateinx.py
author : Raul Saavedra ( raul.saavedra@gmail.com )
Started: 2022.11.18
v1.0   : 2022.12.13
v1.1   : 2022.12.14 (bug-fix for in-passing captures)
v1.1.1 : 2022.12.15 (bug-fixes for in-passing inspection)
v1.2   : 2022.12.17 (1st iterative implementation with option -i)
v1.3   : 2022.12.18 (2st iterative implementation, depth-1st + trim)
v1.4   : 2022.12.29 (3st iterative implementation, debugged)
v1.4.1 : 2023.01.17 (with -a now detects if there are mate-in-Y < X solutions)
v1.5   : 2023.03.01 (additional "supertrim" added)
"""

import sys
import string
import json
import numpy as np
from pathlib import Path
from collections import deque

show_games = False
show_end_games = False
show_attack_footprints = False
show_json = False
verbose = False
max_moves = 2
max_depth = max_moves * 2
wins_per_depth = [0] * max_depth
draws_per_depth = [0] * max_depth
input_file = ''
ngame = 0
nrec_calls = 0
niterations = 0
losing_player = 0
n_1st_moves = 0
n_nodes_in_sol = 0
stop_at_1st_find = True
smateinx = ""
iterative = False
main_stack = deque()
n_trims = 0
shorter_win = False

ORD_CAP_A = ord('A')
ORD_A = ord('a')
ORD_1 = ord('1')
NOPAWN = "KQRNB"
QRNB = "QRNB"
EMPTY_BOARD = " "*64
ZIPSTR  = "     "
ZIPSTRL = len(ZIPSTR)
ZIPCHAR = "_"

PIECE_ENCODE = {"K0": "A",
                "Q0": "B",
                "B0": "C",
                "N0": "D",
                "R0": "E",
                "p0": "F",
                "K1": "G",
                "Q1": "H",
                "B1": "I",
                "N1": "J",
                "R1": "K",
                "p1": "L"}
PIECE_DECODE = {v: k for k, v in PIECE_ENCODE.items()}

EK0 = PIECE_ENCODE["K0"]
EK1 = PIECE_ENCODE["K1"]
EP0 = PIECE_ENCODE["p0"]
EP1 = PIECE_ENCODE["p1"]
EQ0 = PIECE_ENCODE["Q0"]
EQ1 = PIECE_ENCODE["Q1"]
EN0 = PIECE_ENCODE["N0"]
EN1 = PIECE_ENCODE["N1"]
ER0 = PIECE_ENCODE["R0"]
ER1 = PIECE_ENCODE["R1"]

EKINGS=(EK0, EK1)
EPAWNS=(EP0, EP1)
EQUEENS=(EQ0, EQ1)
EKNIGHTS=(EN0, EN1)
EROOKS=(ER0, ER1)

# Pawn attacks from perspective of an attacked king
PATTACKS = {
            EK0: (EP1, ((-1, 1), (1, 1))),
            EK1: (EP0, ((-1, -1), (1, -1))),
            }

PAWN_MOVES = {          # Conditional moves for pawns
    # White pawns
    "p0":   (
            ((-1,1),),  # Only when capturing
            ((0,1),),   # Only when no piece in dest
            ((0,2),),   # Only when at starting row, and no piece in dest
            ((1,1),)    # Only when capturing
            ),
    # Black pawns
    "p1":   (
            ((-1,-1),), # Only when capturing
            ((0,-1),),  # Only when no piece in destination
            ((0,-2),),  # Only when at starting row, and no piece in dest
            ((1,-1),)   # Only when capturing
            ),
    }

# Long linear attacks
#           DIR     xy deltas  Attacking pieces
LATTACKS = {"w" :   (-1, 0,     "QR"),
            "nw":   (-1, 1,     "QB"),
            "n" :   (0, 1,      "QR"),
            "ne":   (1, 1,      "QB"),
            "e" :   (1, 0,      "QR"),
            "se":   (1, -1,     "QB"),
            "s" :   (0, -1,     "QR"),
            "sw":   (-1, -1,    "QB")
            }
# knight attacks
NATTACKS = ((-2,1),(-1,2),(1,2),(2, 1),(2,-1),(1,-2),(-1,-2),(-2,-1))

# Attacks from perspective of the attacking pieces
'''
For each piece type, the valid attacks are stored as a tuple of tuples.
Each subtuple explores a given direction from the piece's position
outwards. Can therefore be scanned until a piece on the board is found
(blocking or getting the attack), then jump to next direction subtuple
'''
ATTACK_MOVES = {
    # White pawns
    "p0":   (
            ((-1,1),),
            ((1,1),)
            ),
    # Black pawns
    "p1":   (
            ((-1,-1),),
            ((1,-1),)
            ),
    # King
    "K":    (
            ((-1,-1),),
            ((-1,0),),
            ((-1,1),),
            ((0,-1),),
            ((0,1),),
            ((1,-1),),
            ((1,0),),
            ((1,1),)
            ),
    # Queen
    "Q":    (
            # Vert N-S
            ((0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7)),
            ((0,-1), (0,-2), (0,-3), (0,-4), (0,-5), (0,-6), (0,-7)),
            # Horiz L-R
            ((1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0)),
            ((-1,0), (-2,0), (-3,0), (-4,0), (-5,0), (-6,0), (-7,0)),
            # Diag NW-SE
            ((-1,1), (-2,2), (-3,3), (-4,4), (-5,5), (-6,6), (-7,7)),
            ((1,-1), (2,-2), (3,-3), (4,-4), (5,-5), (6,-6), (7,-7)),
            # Diag SW-NE
            ((1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)),
            ((-1,-1), (-2,-2), (-3,-3), (-4,-4), (-5,-5), (-6,-6), (-7,-7)),
            ),
    # Rooks
    "R":    (
            # Vert N-S
            ((0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7)),
            ((0,-1), (0,-2), (0,-3), (0,-4), (0,-5), (0,-6), (0,-7)),
            # Horiz L-R
            ((1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0)),
            ((-1,0), (-2,0), (-3,0), (-4,0), (-5,0), (-6,0), (-7,0)),
            ),
    # Bishops
    "B":    (
            # Diag NW-SE
            ((-1,1), (-2,2), (-3,3), (-4,4), (-5,5), (-6,6), (-7,7)),
            ((1,-1), (2,-2), (3,-3), (4,-4), (5,-5), (6,-6), (7,-7)),
            # Diag SW-NE
            ((1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)),
            ((-1,-1), (-2,-2), (-3,-3), (-4,-4), (-5,-5), (-6,-6), (-7,-7)),
            ),
    # Knights
    "N":    (
            ((-2,1),),
            ((-1,2),),
            ((1,2),),
            ((2, 1),),
            ((2,-1),),
            ((1,-2),),
            ((-1,-2),),
            ((-2,-1),)
            )
    }

def get_piece_player(epc):
    # Return the player (0 or 1) for a given encoded piece
    return 1 if epc >= EK1 else 0

class ChessGame:

    def init_from_json(self, game_json):
        self._num = 0
        self._status = ["OK", "OK", "OK", "VALIDATING"]
        self._movep = 0
        self._waitp = 1
        self._board = self._empty_board()
        self._npcs = [0, 0]
        self._nchks = [0, 0]
        self._pcs = [[], []]
        self._can_still_castle = [[False, False], [False, False]]
        self._parent = None
        self._last_move = None
        self._depth = 0
        self._attackfp = [self._no_attackfp(), self._no_attackfp()]
        self._set_board_from_json(game_json)
        self._valid_children = []
        self._winning_children = {}
        self._shorter_winner = False

    def _parse_coords(self, xystr):
        if len(xystr) != 2:
            st = "ERROR: invalid board coordinates '"+xystr+"' " \
                    + "(must be xy, x=a-h, y=1-8)"
            self._status[2] = st
            return None
        x = xystr[0:1]
        y = xystr[1:2]
        if x < 'a' or x > 'h' or y < '1' or y > '8':
            st = "ERROR: invalid board coordinates ("+x+","+y+") in "+xystr
            self._status[2] = st
            return None
        #x,y are text ("a"-"h", "1"-"8") board coordinates
        #i,j are the corresponding (0-7, 0-7) numeric coordinates
        i = ord(x) - ORD_A
        j = int(y) - 1
        return (i, j)

    def _parse_piece(self, pcstr):
        ptype = pcstr[0:1]
        if ptype >= 'a' and ptype <= 'h':
            # Here's a pawn
            ptype = 'p'
            coords = self._parse_coords(pcstr[0:2])
            if coords is None: return None
            y = coords[1]
            if y == 0 or y == 7:
                self._status[2] = "ERROR: invalid pawn position "+pcstr
                return None
        else:
            if not ptype in NOPAWN:
                self._status[2] = "ERROR: invalid piece "+ptype+" in "+pcstr
                return None
            coords = self._parse_coords(pcstr[1:3])
        if coords is None: return None
        return (ptype, coords[0], coords[1])

    def _parse_last_move(self, lastmv_str):
        ''' Last move needs two board coordinates (origin and dest squares)
        in order to be able to tell whether a pawn had moved 2 squares
        as last move right before our input board setup
        '''
        c1 = self._parse_coords(lastmv_str[0:2])
        c2 = self._parse_coords(lastmv_str[2:])
        if c1 is None or c2 is None:
            self._status[2] = "ERROR: invalid last move '" \
                                + lastmv_str+"' (should be of the form 'cRcR')"
            return
        elmpc = self._read_board(c2[0], c2[1])
        if (elmpc == ' ' or PIECE_DECODE[elmpc][1:2] != str(self._waitp)):
            st = "ERROR: last move '"+lastmv_str \
                    + "' in conflict with existing pieces, or turn"
            self._status[2] = st
            return
        # Possible todo: validate that the move is compatible with the
        # piece standing there in c2. It must be either a move doable by
        # the piece itself, or if c2 is at row 7, doable by a pawn
        # promoting into that piece. Otherwise the move is invalid.
        self._last_move = (c1, c2)

    def _set_piece_from_json(self, player, ptype, i, j):
        epiece = PIECE_ENCODE[ptype + str(player)]
        index = i + j*8
        self._board = self._board[0:index] + epiece + self._board[index+1:]
        self._pcs[player].append([epiece, i, j])
        self._npcs[player] += 1

    def _set_board_from_json(self, game_json):
        global losing_player
        self._num = 0
        self._parent = None
        self._depth = 0
        self._nchks = [0, 0]
        self._moves = []
        self._shorter_winner = False
        turn = game_json.get('turn', "?").lower()
        self.set_turn("w" if (turn == "w" or turn == "?") else "b")
        losing_player = 1 - self._movep
        moving_king = EKINGS[self._movep]
        for player in range(2):
            color = "w" if player == 0 else "b"
            pieces = game_json.get(color+"pcs", [])
            counts = {}
            promoted = 0
            for w in pieces:
                piece = self._parse_piece(w)
                if piece == None: return
                ptype = piece[0]
                i = piece[1]
                j = piece[2]
                counts[ptype] = counts.get(ptype, 0) + 1
                if ptype in QRNB:
                    # Count any promoted pieces
                    promoted += (1 if (counts[ptype] >
                                    (1 if ptype == "Q" else 2)) else 0)
                if self._read_board(i, j) != " ":
                    x = chr(ORD_A + i)
                    y = chr(ORD_1 + j)
                    st = "ERROR: two pieces in same position "+x+","+y
                    self._status[player] = st
                    return
                if ptype == "B":
                    # Check that bishops are in different color squares
                    sqcolor = "b" if ((i + j) % 2 == 0) else "w"
                    if counts.get("B"+sqcolor, 0) != 0:
                        # Technically not an error if one of them promoted,
                        # but why would anyone chose a bishop over a queen
                        # for promotion? So this is most likely an error/typo
                        # in the input file
                        st = "ERROR: Two Bishops on same-colored squares"
                        self._status[player] = st
                        return
                    else:
                        counts["B"+sqcolor] = 1
                self._set_piece_from_json(player, ptype, i, j)
            if counts.get("K", 0) != 1:
                st = "ERROR: "+str(counts.get("K",0))+" King pieces" \
                        " for " + color + " player"
                self._status[player] = st
                return
            if counts.get("p", 0) > 8:
                st = "ERROR: "+str(counts["p"])+" pawns for " \
                        + color + " player"
                self._status[player] = st
                return
            if promoted > (8 - counts.get("p", 0)):
                st = "ERROR: "+str(counts.get("p", 0))+" pawns " \
                        + str(promoted) + " promoted pieces, " \
                        + "too many for " + color + " player"
                self._status[player] = st
                return
            self._sort_pieces(player)
        self._last_move = None
        lastmv_str = game_json.get('lastMove', "")
        if (not lastmv_str is None) and lastmv_str != "":
            self._parse_last_move(lastmv_str)
            if self._last_move is None: return
        self._gen_all_attack_footps()
        self._check_castles()

    def _gen_all_attack_footps(self):
        # All pieces now on board, generate their attack foot prints
        for player in range(2):
            for pxy in self._pcs[player]:
                epc = pxy[0]        # Encoded piece (1 char)
                i = pxy[1]
                j = pxy[2]
                dpc = PIECE_DECODE[epc]     # Decoded piece (2 chars)
                vp = dpc if dpc[0:1] == "p" else dpc[0:1]
                vmoves = ATTACK_MOVES.get(vp, [])
                afp = self._attackfp[player]
                for movedir in vmoves:
                    for m in movedir:
                        ii = i + m[0]
                        if ii < 0 or ii > 7: break
                        jj = j + m[1]
                        if jj < 0 or jj > 7: break
                        afp[ii][jj] += 1
                        # Here check if board has a piece here, and if so
                        # stop checking any further in this attacking dir
                        if self._read_board(ii, jj) != " ": break

    def _read_board(self, i, j):
        index = i + j * 8
        return self._board[index:index+1]

    def _write_board(self, board, i, j, vchar):
        index = i + j * 8
        return board[0:index] + vchar + board[index+1:]

    def _gen_new_board(self, oldboard, piece, idx_from, idx_to):
        newBoard = oldboard[0:idx_from] \
                    + " " \
                    + oldboard[idx_from+1:]
        newBoard = newBoard[0:idx_to] \
                    + piece \
                    + newBoard[idx_to+1:]
        ''' Here we simply move one piece from one position to another,
        replacing the starting position with a space, and replacing
        whatever was in the destination with the moved piece.
        Notice here we do not handle a pawn captured in passing, that
        gets handled both in the simulated move (board-wise), and
        in init_from_parent_game (enemy pieces-wise)
        '''
        return newBoard

    def _sort_pieces(self, player):
        self._pcs[player].sort()

    def init_from_parent_game(self, pgame, pmove, child_board):
        # Generate ChildGame's board from parent one + move
        self._status = ["OK", "OK", "OK", "Exploring"]
        # For now keep the same moving player as from parent game
        self.set_turn(pgame.get_turn())
        self._parent = pgame
        self._num = -1
        self._depth = pgame._depth + 1
        self._last_move = pmove
        self._board = child_board
        self._pcs = [[], []]
        self._npcs = [0, 0]
        self._nchks = [0, 0]
        self._moves = []
        self._valid_children = []
        self._winning_children = {}
        self._shorter_winner = False
        # moving piece from old square at i0, j0 ...
        oldsq = pmove[0]
        i0 = oldsq[0]
        j0 = oldsq[1]
        # ... to new square at i1, j1
        newsq = pmove[1]
        i1 = newsq[0]
        j1 = newsq[1]
        # moving piece
        empc = pgame._read_board(i0, j0)    # Encoded moved piece
        in_passing_capture = False
        deltax = i1 - i0
        if empc in EPAWNS:
            if deltax != 0:
                # Moved piece was a pawn and captured something (moved
                # diagonally.) Check if it was an in-passing capture
                # of another pawn
                in_passing_capture = pgame._read_board(i1, j1) == ' '
        ''' Clone pieces for our soon moving player from parent game's
        waiting player, except that one piece (if any) which might
        have been in the destination square (such a piece would be
        getting captured by this move)
        '''
        castle = False
        if empc in EKINGS:
            # King moving
            if (deltax == 2 or deltax == -2):
                # It's a castle move
                castle = True
                if (verbose):
                    print("***** " + PIECE_DECODE[empc] \
                            + " doing a " \
                            + ("short" if deltax == 2 else "long") \
                            + " castle move *****")
                eprook = EROOKS[pgame._movep]
            self._can_still_castle = [[], []]
            # Clone waiting player's castle possibilities from parent
            self._can_still_castle[pgame._waitp] = \
                pgame._can_still_castle[pgame._waitp]
            # But disable castles from now on for the moving player
            self._can_still_castle[pgame._movep] = (False, False)
        else:
            # Clone castle possibilities from parent game
            self._can_still_castle = [
                [pgame._can_still_castle[0][0],
                 pgame._can_still_castle[0][1]],
                [pgame._can_still_castle[1][0],
                 pgame._can_still_castle[1][1]]]
            if empc in EROOKS:
                # Rook moving
                if i0 == 0 or i0 == 7:
                    # But disable castle on this rook's side for moving player
                    rkside = (0 if i0 == 0 else 1)
                    self._can_still_castle[pgame._movep][rkside] = False
        capture = 0
        for p in pgame._pcs[pgame._waitp]:
            px = p[1]
            py = p[2]
            if px == i1 and (py == j1 or (py == j0 and in_passing_capture)):
                # This piece just got captured
                capture = 1
                continue
            new_p = [p[0], px, py]
            self._pcs[pgame._waitp].append(new_p)
        # Clone pieces for our soon waiting player from parent's game
        # moving player
        for p in pgame._pcs[pgame._movep]:
            px = p[1]
            py = p[2]
            if px == i0 and py == j0:
                # This is the moving piece. Use the piece encoded
                # in the new board, which will be different from the
                # original in the case of a pawn promotion
                empc = self._read_board(i1, j1)
                new_p = [empc, i1, j1]
                if empc != p[0] and verbose:
                    print("***** After game " + str(pgame.get_num()) \
                        + " a promotion into "+PIECE_DECODE[empc] \
                        + " took place at "+str(i1)+","+str(j1)+" *****")
            else:
                if castle and p[0] == eprook and \
                    ((deltax < 0 and px == 0) or (deltax > 0 and px == 7)):
                    # This is the castling rook, move it accordingly
                    new_p = [eprook, px + (3 if deltax < 0 else -2), py]
                else:
                    new_p = [p[0], px, py]
            self._pcs[pgame._movep].append(new_p)
        self._npcs[pgame._movep] = pgame._npcs[pgame._movep]
        self._npcs[pgame._waitp] = pgame._npcs[pgame._waitp] - capture
        self._attackfp = [self._no_attackfp(), self._no_attackfp()]
        self._gen_all_attack_footps()

    def _check_castles(self):
        for np in range(2):
            row = np * 7
            if self._read_board(4, row) != EKINGS[np]:
                # King not in starting position -> moving player can't castle
                continue
            if self._read_board(0, row) == EROOKS[np]:
                # Rook there, asume long castle (0-0-0) still possible
                self._can_still_castle[np][0] = True
            if self._read_board(7, row) == EROOKS[np]:
                # Rook there, asume short castle (0-0) still possible
                self._can_still_castle[np][1] = True

    def get_parent_game(self):
        return self._parent

    def _empty_board(self):
        return EMPTY_BOARD

    def get_board(self):
        return self._board

    def _no_attackfp(self):
        return np.zeros([8,8])

    def simulate_move(self, m):
        ''' Returns a list of children boards given a move.
        Typically just 1 board inside that list, but 2 when
        promoting a pawn: one for promoting into queen, and one into knight.
        (Never promoting into rooks or bishops, since they are never
        preferable over a Queen.)
        '''
        xold = m[0][0]
        yold = m[0][1]
        index_old = xold + yold * 8
        xnew = m[1][0]
        ynew = m[1][1]
        index_new = xnew + ynew * 8
        # Encoded moving piece
        empc = self._board[index_old:index_old+1]
        if empc in EPAWNS:
            if (ynew == 0 or ynew == 7):
                # Pawn reaching a final row, so a promotion applies.
                prom_q = EQUEENS[self._movep]
                prom_n = EKNIGHTS[self._movep]
                ch_board_q = self._gen_new_board(
                                self._board,
                                prom_q,
                                index_old,
                                index_new)
                ch_board_n = self._gen_new_board(
                                self._board,
                                prom_n,
                                index_old,
                                index_new)
                return (ch_board_q, ch_board_n)
            else:
                # Simply move the pawn from old to new position
                ch_board = self._gen_new_board(
                                self._board,
                                empc,
                                index_old,
                                index_new)
                if xnew != xold:
                    # Pawn moved diagonally, so it captured something.
                    # If it was an in-passing capture we must remove
                    # that captured pawn from the new board setup
                    if self._read_board(xnew, ynew) == ' ':
                        # It was an in-passing capture, so remove
                        # the captured pawn from board
                        ch_board = self._write_board(ch_board, xnew, yold, ' ')
                return (ch_board,)
        else:
            # Just move the piece from old to new position
            ch_board = self._gen_new_board(
                            self._board,
                            empc,
                            index_old,
                            index_new)
            if empc in EKINGS:
                j = m[0][1]*8   # Start of king's row on the board
                deltax = m[1][0] - m[0][0]
                if deltax == -2:
                    # Move was a O-O-O (long castle)
                    # so move also this player's left rook
                    ch_board = self._gen_new_board(
                                ch_board,
                                EROOKS[self._movep],
                                j, j+3)
                elif deltax == 2:
                    # Move was a O-O (short castle)
                    # so move also this player's right rook
                    ch_board = self._gen_new_board(
                                ch_board,
                                EROOKS[self._movep],
                                j+7, j+5)
            return (ch_board,)

    #def set_num(self, num, depth):
    def set_num(self, num):
        self._num = num
        #self._depth = depth

    def get_num(self):
        return self._num

    def get_depth(self):
        return self._depth

    def add_valid_child(self, child_game):
        self._valid_children.append(child_game)

    def get_last_child(self):
        return self._valid_children[len(self._valid_children) - 1]

    def get_valid_children(self):
        return self._valid_children

    def get_num_valid_children(self):
        return len(self._valid_children)

    def clear_valid_children(self):
        self._valid_children.clear()

    def generate_all_moves(self):
        # Generate list of all valid moves to consider
        king_moves = []
        # The king is always among the pieces to consider
        self._append_king_moves(king_moves)
        nchecks = self.count_all_checks()
        if nchecks < 2:
            pawn_moves = []
            opcs_moves = []
            # Not under double check, so consider non-king movements
            npieces = len(self._pcs[self._movep])
            for i in range(1, npieces, 1):
                p = self._pcs[self._movep][i]
                dp = PIECE_DECODE[p[0]]
                dpt = dp[0:1]
                i = p[1]
                j = p[2]
                if dpt == "p":
                    self._append_pawn_moves(pawn_moves, dp, i, j)
                else:
                    self._append_opcs_moves(opcs_moves, dpt, i, j)
            self._moves = pawn_moves + king_moves + opcs_moves
        else:
            self._moves = king_moves
        self._last_move_idx = len(self._moves) - 1
        self._next_move = 0
        return self._moves

    def get_next_move(self):
        if self._next_move > self._last_move_idx:
            return None
        move = self._moves[self._next_move]
        self._next_move += 1
        return move

    def _decode_piece_from_board(self, i, j):
        p = self._read_board(i,j)
        if p == " ": return "  "
        return PIECE_DECODE[p]

    def set_turn(self, turn):
        if turn == "b":
            self.set_mover(1)
        else:
            self.set_mover(0)

    def set_mover(self, p):
        if p == 1:
            self._movep = 1     # moving player
            self._waitp = 0     # waiting player
        else:
            self._movep = 0
            self._waitp = 1

    def get_mover(self):
        return self._movep

    def get_waiter(self):
        return self._waitp

    def flip_turn(self):
        if self._movep == 0:
            self.set_mover(1)
        else:
            self.set_mover(0)

    def get_turn(self):
        return "w" if self._movep == 0 else "b"

    def get_next_turn(self):
        return "b" if self._movep == 0 else "w"

    def get_npcs(self, player):
        return self._npcs[player]

    def get_num_checks(self, player):
        return self._nchks[player]

    def get_status(self):
        if (self._status[0] == "OK"
            and self._status[1] == "OK"
            and self._status[2] == "OK"):
            self._status[3] = "OK"
            return "OK"
        self._status[3] = "INVALID"
        return ("Whites  : "+self._status[0] + "\n"
                + "Blacks  : "+self._status[1] + "\n"
                + "Gameplay: "+self._status[2] + "\n"
                + "Overall : "+self._status[3])

    def set_ending(self, msg):
        self._status[3] = msg

    def get_path_from_root(self):
        if self._parent is None:
            return ([] if self._last_move is None else [self._last_move])
        else:
            path = self._parent.get_path_from_root()
            path.append(self._last_move)
            return path

    def _count_pawn_checks(self, eking, kx, ky):
        pattacks = PATTACKS[eking]
        epawn = pattacks[0]
        la = pattacks[1]
        for pos in la:
            x = kx + pos[0]
            y = ky + pos[1]
            if x >= 0 and x < 8 and y >= 0 and y < 8:
                if self._read_board(x, y) == epawn:
                    # Enemy pawn checking this king
                    # print("p"+self._swaitp+" at "+chr(ORD_A+x)+",",
                    #           chr(ORD_1+y)+" CHECKING "+dking)
                    return 1
        return 0

    def _count_long_checks(self, eking, kx, ky):
        nla_chks = 0
        for adir, ainfo in LATTACKS.items():
            xdelta = ainfo[0]
            ydelta = ainfo[1]
            apieces = ainfo[2]
            scanx = kx + xdelta
            scany = ky + ydelta
            while scanx >= 0 and scanx < 8 and scany >= 0 and scany < 8:
                square = self._read_board(scanx, scany)
                if square == " ":
                    scanx = scanx + xdelta
                    scany = scany + ydelta
                    continue
                # Piece found in this attack direction
                if get_piece_player(square) == self._movep: break
                # It's an enemy piece
                piece = PIECE_DECODE[square]
                ptype = piece[0:1]
                if ptype in apieces:
                    # And it attacks in this direction, checking our king
                    nla_chks += 1
                #else: Enemy piece there, but does not attack our
                # king in this dir -> fine to move on to next dir
                break
        return nla_chks

    def _count_knight_checks(self, eking, kx, ky):
        lnpos = NATTACKS
        nk_chks = 0
        for pos in lnpos:
            scanx = kx + pos[0]
            scany = ky + pos[1]
            if scanx < 0 or scanx > 7 or scany < 0 or scany > 7: continue
            square = self._read_board(scanx, scany)
            if square == " ": continue
            if get_piece_player(square) == self._movep: continue
            if square in EKNIGHTS:
                # There's an enemy knight there checking our king
                nk_chks += 1
        return nk_chks

    def count_all_checks(self):
        # Scan all attacks from the playing King's point of view
        king = self._pcs[self._movep][0]
        eking = king[0]
        kx = king[1]
        ky = king[2]
        nchks = (self._count_pawn_checks(eking, kx, ky)
                + self._count_long_checks(eking, kx, ky)
                + self._count_knight_checks(eking, kx, ky))
        self._nchks[self._movep] = nchks
        return nchks

    def _append_king_moves(self, moves):
        king = self._pcs[self._movep][0]
        i = king[1]
        j = king[2]
        ''' When castling we will add here just the king's move,
        but when applying it in a simulated move, a 2-square horiz.
        move for a king will be detected, and the corresponding
        rook will also be moved there to complete the castle.
        '''
        if self._can_still_castle[self._movep][0]:
            if self._can_long_castle_now(j):
                moves.append( ((i,j), (i-2,j)) )
        if self._can_still_castle[self._movep][1]:
            if self._can_short_castle_now(j):
                moves.append( ((i,j), (i+2,j)) )
        amoves = ATTACK_MOVES.get("K")
        a = self._attackfp[self._waitp]
        for movedir in amoves:
            for m in movedir:
                ii = i + m[0]
                if ii < 0 or ii > 7: break
                jj = j + m[1]
                if jj < 0 or jj > 7: break
                square = self._read_board(ii, jj)
                if square != " ":
                    if get_piece_player(square) == self._movep:
                        # A piece of ours is there, move on to next dir
                        break
                if a[ii][jj] > 0:
                    # Square is out of bounds for our king, skip
                    continue
                # Otherwise add the move as valid
                newmove = ((i,j), (ii,jj))
                moves.append(newmove)

    def _can_long_castle_now(self, row):
        a = self._attackfp[self._waitp]
        return (a[2][row] == 0 and a[3][row] == 0 and a[4][row] == 0
            and self._read_board(1,row) == ' '
            and self._read_board(2,row) == ' '
            and self._read_board(3,row) == ' ')

    def _can_short_castle_now(self, row):
        a = self._attackfp[self._waitp]
        return (a[4][row] == 0 and a[5][row] == 0 and a[6][row] == 0
            and self._read_board(5,row) == ' '
            and self._read_board(6,row) == ' ')

    def _append_opcs_moves(self, moves, ptype, i, j):
        amoves = ATTACK_MOVES.get(ptype)
        for movedir in amoves:
            for m in movedir:
                ii = i + m[0]
                if ii < 0 or ii > 7: break
                jj = j + m[1]
                if jj < 0 or jj > 7: break
                square = self._read_board(ii, jj)
                if square != " ":
                    if get_piece_player(square) == self._movep:
                        # A piece of ours is there, move on to next dir
                        break
                # Otherwise add the move as valid
                newmove = ((i,j), (ii,jj))
                moves.append(newmove)
                if square != " ":
                    # Destination square is occupied, no point exploring
                    # this moving direction any further
                    break

    def _append_pawn_moves(self, moves, dp, i, j):
        # Pawns require very special movement considerations
        pmoves = PAWN_MOVES.get(dp)
        for movedir in pmoves:
            for m in movedir:
                ii = i + m[0]
                if ii < 0 or ii > 7: break
                jj = j + m[1]
                if jj < 0 or jj > 7: break
                square = self._read_board(ii, jj)
                if m[0] == 0:
                    # Only move vertically if path to dest square is free
                    if square != " ": continue
                    m1 = m[1]
                    if m1 == 2:
                        if j != 1 and self._movep == 0:
                            # Our pawn is not in its starting raw so
                            # it can't do a 2-step move
                            continue
                        if self._read_board(ii, j + 1) != " ":
                            # Path is not clear for the pawn to move 2 sq
                            continue
                    elif m1 == -2:
                        if j != 6 and self._movep == 1:
                            continue
                        if self._read_board(ii, j - 1) != " ":
                            continue
                    #else
                        # Pawn is just moving 1 square forward
                else:
                    # Moving diagonally
                    if square != " ":
                        # The square is occupied
                        if get_piece_player(square) == self._movep:
                            # A piece of ours is in that square, so
                            # skip this move
                            continue
                    else:
                        # Moving diagonally into an empty square is only
                        # valid when capturing "in passing," e.g. a 2-square
                        # moving enemy pawn that just moved next to ours.
                        # We have to identify this possibility here
                        if ((jj != 5 and self._movep == 0) or
                            (jj != 2 and self._movep == 1)):
                            # Our pawn is not in the right raw to be able
                            # to capture a 2-moving pawn
                            continue
                        squareAdj = self._read_board(ii, j)
                        if squareAdj == " ":
                            # The square right next to our pawn is free
                            continue
                        if squareAdj != EPAWNS[self._waitp]:
                            # There is a piece there, but it's not
                            # an enemy pawn
                            continue
                        # Here our pawn was in the right row, and next
                        # to it there is an enemy pawn!
                        if (self._last_move is None
                            or self._last_move[1][0] != ii
                            or self._last_move[1][1] != j):
                            # Last move was not made by that pawn
                            continue
                        # This enemy pawn did make the very last move
                        enemy = get_piece_player(squareAdj)
                        epoy = self._last_move[0][1]
                        if ((enemy == 1 and epoy != 6)
                            or (enemy == 0 and epoy != 1)):
                            # But it was not a 2-square pawn move
                            continue
                        # Last move was made by that enemy pawn, and
                        # it was a 2-square move, so our pawn can
                        # indeed capture it in passing
                        if verbose:
                            print("***** Detected pawn captured " \
                                + "'in-passing'  *****")
                newmove = ((i,j), (ii,jj))
                moves.append(newmove)

    def tell_parent_iam_awin(self):
        global n_1st_moves, stop_at_1st_find, smateinx, shorter_win
        pgame = self._parent
        if not pgame is None:
            pgame._winning_children[self] = self._depth
            if pgame._parent is None:
                # pgame (self's parent node) is the root node
                n_1st_moves += 1
                if stop_at_1st_find:
                    # Fully printout this first solution found, and exit
                    print("\nFound a " + smateinx + " solution!")
                    show_final_summary(pgame)
                    exit()
                else:
                    # show only the starting winning move, and keep searching
                    # for other possible solutions
                    print("\nFound " + str(n_1st_moves) + " " + smateinx \
                        + " solution(s)!  Winning first move: ", end="")
                    self._shorter_winner = \
                        self.has_shorter_wsubtree(True, max_depth -2)
                    if (self._shorter_winner):
                        shorter_win = True
                    self.print_winning_tree("", False)

    def has_shorter_wsubtree(self, all, mdepth):
        ''' Finds out if a mate-in-Y is possible,
        with Y < the requested X max_moves
        '''
        if (len(self._winning_children) == 0):
            return True
        if (mdepth == 1):
            return False
        justone = not all
        mminus1 = mdepth - 1
        if all:
            for child in self._winning_children.keys():
                if (not child.has_shorter_wsubtree((not all), mminus1)):
                    return False
            return True
        else:
            for child in self._winning_children.keys():
                if (child.has_shorter_wsubtree((not all), mminus1)):
                    return True
            return False

    def get_winning_children(self):
        return self._winning_children

    def print_winning_tree(self, tabs, all):
        global n_nodes_in_sol
        lm = self._last_move
        if lm == None:
            dmove = "?"
            n_nodes_in_sol = -1
        else:
            ox = lm[0][0]
            oy = lm[0][1]
            nx = lm[1][0]
            ny = lm[1][1]
            empc = self._read_board(nx, ny)
            deltax = nx - ox
            if empc in EKINGS and (deltax == 2 or deltax == -2):
                # Castle move
                dmove = "0-0" if deltax == 2 else "0-0-0"
            else:
                # Add final piece with old coordinates
                dmove = chr(ORD_A + ox) + str(oy + 1)
                if self._parent != None:
                    eopc = self._parent._read_board(ox, oy)
                    if eopc != empc:
                        # Different piece, so move had a pawn promotion
                        dmove = PIECE_DECODE[eopc] + dmove
                    else:
                        dmove = PIECE_DECODE[empc] + dmove
                    if " " != self._parent._read_board(nx, ny) or \
                        ((empc in EPAWNS) and deltax != 0):
                        # Move had a capture involved
                        dmove += "x"
                    # Add new coordinates after the move
                    dmove = dmove + chr(ORD_A + nx) + str(ny + 1)
                    if eopc != empc:
                        # Show the new promoted piece
                        dmove += "=" + PIECE_DECODE[empc]
                else:
                    # Add piece and new coordinates
                    dmove = PIECE_DECODE[empc] + dmove \
                        + chr(ORD_A + nx) + str(ny + 1)
            if self._status[3].startswith("WIN"):
                # Checkmate caused by the move
                dmove += "#"
            elif self._nchks[self._movep] > 0:
                # Check caused by the move
                dmove += "+"
        shwinner = ""
        if (self._shorter_winner):
            shwinner = " (-> Mate-in-X < " + str(max_moves) + " !!!)"
        if all:
            n_nodes_in_sol += 1
            tail_txt = " " * max(2, 30 - len(tabs) - len(dmove)) \
                        + " (" + str(n_nodes_in_sol) + ")" + shwinner
            print(tabs + dmove + tail_txt)
            for kchild in self._winning_children.keys():
                kchild.print_winning_tree(tabs+"    ", all)
        else:
            print(tabs + dmove + shwinner)

    def has_winning_children(self):
        return self.get_num_winning_children() > 0

    def get_num_winning_children(self):
        return len(self._winning_children.keys()) > 0

    def show(self, show_attack_fp):
        nums = \
            "        0      1      2      3      4      5      6      7"
        letters = \
            "        a      b      c      d      e      f      g      h"
        horiz = "    " \
            + "+------+------+------+------+------+------+------+------+"
        print("\n" + letters)
        for j in range(8):
            print(horiz)
            print("    ", end="")
            whitesq = (j % 2 == 0)
            for i in range(8):
                if whitesq:
                    print("|      ", end="")
                else:
                    print("|######", end="")
                whitesq = not whitesq
            print("|")
            print("  {0} ".format(8-j), end="")
            for i in range(8):
                piece = self._decode_piece_from_board(i, 7-j)
                if whitesq:
                    print("|  "+piece+"  ", end="")
                else:
                    print("|[ "+piece+" ]", end="")
                whitesq = not whitesq
            print("| {0}".format(7-j))
            print("    ", end="")
            for i in range(8):
                if show_attack_fp:
                    print("|", end="")
                    wattacks = int(self._attackfp[0][i][7-j])
                    if wattacks != 0:
                        print(f"{wattacks:1d}", end="")
                    else:
                        print(" ", end="")
                    print("    ", end="")
                    battacks = int(self._attackfp[1][i][7-j])
                    if battacks != 0:
                        print(f"{battacks:1d}", end="")
                    else:
                        print(" ", end="")
                else:
                    if whitesq:
                        print("|      ", end="")
                    else:
                        print("|######", end="")
                whitesq = not whitesq
            print("|")
        print(horiz)
        print(nums)
        print(letters)
        print("\tPossible castle moves:", \
                "w:" + (" 0-0-0 "
                    if self._can_still_castle[0][0] else " ") \
                + ("0-0"
                    if self._can_still_castle[0][1] else "") \
                + "  b:" + (" 0-0-0 "
                    if self._can_still_castle[1][0] else " ") \
                + ("0-0"
                    if self._can_still_castle[1][1] else ""))
        print("\tTo play: "+self.get_turn()+"    ", end="")
        print("Checked: w="+str(self._nchks[0])+" b=" \
                + str(self._nchks[1]) + "     ", end="")
        print("Move history:\n", end="")
        print(self.get_path_from_root(), end="")
        #print("\nWhite pieces:", self._pcs[0])
        #print("Black pieces:", self._pcs[1])
        print("\nGame #"+str(self._num), \
                "(depth "+str(self._depth)+")", self._status[3])

    def show_board(self):
        print(self._num, "(@", self._depth,") : ", self._board)


BAR = '='*48

def starting_banner():
     print("\n"+BAR)
     print('|      mateinx.py v1.5                         |')
     print('|      By Raul Saavedra F., 2023-Mar-01        |');
     print(BAR)

def load_game_from_json():
    with open(input_file, 'r') as f:
        game_json = json.load(f)
    g = game_json['chess-game']
    print("Starting game (json input): "+input_file)
    if show_json:
        print(json.dumps(game_json, indent=4)+"\n")
    return g

def evaluate_iteratively(starting_game):
    global ngame, nrec_calls, losing_player, max_depth
    global show_games, show_attack_footprints, verbose, niterations, n_trims
    main_stack.append( starting_game )
    while len(main_stack) > 0:
        niterations += 1
        game = main_stack[len(main_stack) - 1]
        if game.get_depth() >= max_depth:
            main_stack.pop()
            continue
        if game.get_num() < 0:
            # First time seeing this game from the stack
            game.set_num(ngame)
            if show_games and ngame % 1000 == 0 and ngame > 0:
                game.show(show_attack_footprints)
            if verbose and ngame % 50000 == 0:
                print("Games explored:", ngame)
            ngame += 1
            game.generate_all_moves()
        if (game.get_mover() == losing_player and
            game.get_num_valid_children() > 0 and
            game.get_last_child().get_num_winning_children() == 0):
            # Speed-up analogous to the one done in the recursive:
            n_trims += 1
            main_stack.pop()
            continue
        m = game.get_next_move()
        if m is None:
            # All children of this game already processed, so remove from
            # stack and verify this game itself
            main_stack.pop()
            verify(game, game.get_valid_children())
            game.clear_valid_children()
        else:
            # Simulate move to get corresponding child(ren) board(s)
            child_boards = game.simulate_move(m)
            for ch_brd in child_boards:
                # Generate new child(ren) given the move, and explore further
                child_game = ChessGame()
                child_game.init_from_parent_game(game, m, ch_brd)
                nchks_in_child = child_game.count_all_checks()
                if nchks_in_child > 0:
                    # King left in check with this move: invalid.
                    # See comment in the recursive version for more details
                    break
                child_game.flip_turn()
                game.add_valid_child(child_game)
                main_stack.append(child_game)
    return

def evaluate_recursively(parent, game, depth):
    global ngame, nrec_calls, losing_player
    global show_games, show_attack_footprints, verbose, n_trims
    nrec_calls += 1
    if depth >= max_depth:
        return
    game.set_num(ngame)
    if show_games and ngame % 1000 == 0 and ngame > 0:
        game.show(show_attack_footprints)
    if verbose and ngame % 50000 == 0:
        print("Games explored:", ngame)
    ngame += 1
    moves = game.generate_all_moves()
    mov_player = game.get_mover()
    next_depth = depth + 1
    valid_children = []
    for m in moves:
        # Simulate move to get corresponding child(ren) board(s)
        child_boards = game.simulate_move(m)
        for ch_brd in child_boards:
            # Generate new child(ren) given the move, and explore further
            child_game = ChessGame()
            child_game.init_from_parent_game(game, m, ch_brd)
            nchks_in_child = child_game.count_all_checks()
            if nchks_in_child > 0:
                ''' Our King is left in check with this move: invalid.
                We can break from the inner for already since it will
                iterate a second time only when promoting a pawn, but
                regardless of promoting into Queen or Knight, if the
                first promotion is invalid, the second will be as well
                '''
                break
            valid_children.append(child_game)
            child_game.flip_turn()
            evaluate_recursively(game, child_game, next_depth)
            if (mov_player == losing_player and
                child_game.get_num_winning_children() == 0):
                ''' If parent game moving player (mov_player) is the
                "losing" player (that is, not the 1st moving player in
                the mate-in-x setup,)
                and at least one child here has no winning moves for the
                "winning" player,
                then this move of the losing player is one survival path.
                This child game's parent is therefore for sure not in a
                winning path for the 1st mover, so no need to explore
                additional moves here.
                This simple check can trim down the entire search space
                hugely (e.g. orders of magnitude in some cases)
                '''
                n_trims += 1
                return

            if (stop_at_1st_find):
                ''' And another "super" trimming: Given that we are not
                trying to find absolutely all alternative winning
                solutions in this run (no -a option,) if there's a
                winning child already found by the winning player, then
                that one can do; we do not need to look for additional
                ones among its siblings. This trim alone also can cut
                down the total execution time once again by orders of
                magnitude, e.g. for game-17.json (a mate-in-5,) now
                takes < 1 minute, before it took ~19 mins!
                '''
                if ((mov_player != losing_player) and
                    (game.get_num_winning_children() > 0)):
                    n_trims += 1
                    return;

    # We verify the game after checking all moves of the moving player
    verify(game, valid_children)
    return

def verify(game, children):
    global ngame, wins_per_depth, draws_per_depth, show_end_games
    depth = game.get_depth()
    if children == []:
        nchks = game.get_num_checks(game.get_mover())
        if nchks > 0:
            '''If no moves, and under check, the moving player has
            lost. Notify the parent game that this game is the
            result of a winning move (in fact a mate-in-1 move
            for the parent game's moving player.)
            Parent game then will know that at least one of
            his moves was a winning one.
            '''
            winner = game.get_next_turn()
            wins_per_depth[depth] += 1
            msg = "WIN for " + winner + ", game #" \
                    + str(game.get_num()) + ", depth " + str(depth)
            game.set_ending(msg)
            game.tell_parent_iam_awin()
            if show_end_games: game.show(show_attack_footprints)
            return

        # No moves and not under check -> Game over: DRAW
        draws_per_depth[depth] += 1
        msg = "DRAW found at game #" + str(ngame) \
                + ", depth " + str(depth)
        game.set_ending(msg)
        if show_end_games: game.show(show_attack_footprints)
        return

    if game.get_npcs(0) + game.get_npcs(1) == 2:
        draws_per_depth[depth] += 1
        msg = "GAME OVER: DRAW (only both Kings remain)," \
            +" game #" + str(game.get_num()) + ", depth " + str(depth)
        game.set_ending(msg)
        if show_end_games: game.show(show_attack_footprints)
        return

    # Reaching this point means player had move options
    for child in children:
        if child.get_num_winning_children() == 0:
            return

    ''' Reaching this point means absolutely all children had
    at least one winning move (for the opponent's win.) So
    let this node know that all its children have at least
    one winning move, and notify parent of this game that this
    game itself is the result of a winning move.
    '''
    for child in children:
        child.tell_parent_iam_awin()
    game.tell_parent_iam_awin()
    return

def process_options(argv):
    global input_file, verbose, show_attack_footprints
    global show_json, show_games, show_end_games, max_moves, max_depth
    global wins_per_depth, draws_per_depth, stop_at_1st_find, iterative
    for opt in argv:
        if opt == "-h":
            # Display help
            with open('mateinx-usage.txt') as help:
                for line in help:
                    print(line.rstrip())
            exit()
        if opt == "-a":
            stop_at_1st_find = False
            print("Searching for ALL solutions (won't stop after 1st find)")
            continue
        if opt == "-g":
            show_games = True
            print("Showing some game boards while searching")
            continue
        if opt == "-e":
            print("Showing End-game boards (Wins and Draws)")
            show_end_games = True
            continue
        if opt == "-c":
            show_attack_footprints = True
            print("Showing attack footprint counts on board squares")
            continue
        if opt == "-v":
            verbose = True
            print("Running in verbose mode")
            continue
        if opt == "-j":
            show_json = True
            print("Showing json file in the output")
            continue
        if opt == "-i":
            iterative = True
            print("Using Iterative instead of recursive implementation")
            continue
        if opt[0:2] == "-m":
            # Set maximum # moves to explore
            n = opt[2:]
            if n.isdecimal() and int(n) >= 0:
                max_moves = int(n)
                max_depth = max_moves * 2
                wins_per_depth = [0] * max_depth
                draws_per_depth = [0] * max_depth
            else:
                print("Invalid max moves parameter:", n)
            print("Using", max_moves, "as maximum number of moves " \
                    + "(max depth=" + str(max_depth) + ")")
            continue
        if ((not opt.startswith("-")) and (input_file == "")):
            # This should be the file name (.json) to use as input
            fname = opt
            vpath = Path(fname)
            if vpath.is_file():
                input_file = fname
                if verbose: print("Using '"+input_file+"' as input file")
            else:
                print("ERROR: file '"+fname+"' not found, exiting")
                exit(-2)
            continue
        print("ERROR: "+opt+" is not an option, use -h for usage details")
        exit(-1)

def show_final_summary(game):
    global ngame, nrec_calls, ngame, wins_per_depth, draws_per_depth
    global smateinx, n_nodes_in_sol, n_1st_moves, iterative, shorter_win
    if (game.has_winning_children()):
        print("\n" + smateinx + " tree of moves:")
        game.print_winning_tree("", True)
        print("\nTotal number of nodes in solution:", n_nodes_in_sol)
        print("Found " + str(n_1st_moves) + " first move(s) which can " \
                + smateinx + ":")
        for ch in game.get_winning_children():
            ch.print_winning_tree("    ", False)
    else:
        if (wins_per_depth[0] == 1):
            print("\nInitial board already has a checkmate.")
        else:
            print("\nNo moves for " + game.get_turn() \
                    + " found to " + smateinx)
    print("\nWins  found per depth:", wins_per_depth)
    print("Draws found per depth:", draws_per_depth)
    if iterative:
        print("Total iterations     :", niterations)
    else:
        print("Total recursive calls:", nrec_calls)
    print("Total search trims   :", n_trims)
    print("Total games processed:", ngame)
    if (shorter_win):
        print("\nNOTE: Mate-in-X < " + str(max_moves) \
            + " moves were found!!!  Retry with -m" \
            + str(max_moves - 1) + "\n")

def mateinx_solver(argv):
    global ngame, verbose, nrec_calls, max_moves, wins_per_depth
    global draws_per_depth, show_games, show_attack_footprints
    global n_1st_moves, n_nodes_in_sol, smateinx, input_file, iterative
    starting_banner()
    process_options(argv)
    if input_file == "":
        print("No input file argument, use -h for usage details.")
        exit(-3)
    try:
        json_data = load_game_from_json()
    except:
        print("\nERROR parsing json file '" + input_file + "'")
        print("Please verify the file contents.\n" \
                + "Examples available at: github.com/rsaavedraf/checkmate-in-x\n")
        exit(-4)
    game = ChessGame()
    game.init_from_json(json_data)
    vst = game.get_status()
    if vst != "OK":
        if show_games: game.show(False)
        print(vst)
        exit()
    # Aditional validations before starting recursive calls
    orig_turn = game.get_turn()
    game.set_turn("w")
    nchk0 = game.count_all_checks()
    vst = game.get_status()
    if vst != "OK":
        if show_games: game.show(False)
        print(vst)
        exit()
    game.set_turn("b")
    nchk1 = game.count_all_checks()
    vst = game.get_status()
    if vst != "OK":
        if show_games: game.show(False)
        print(vst)
        exit()
    if nchk0 > 0 and nchk1 > 0:
        if show_games: game.show(show_attack_footprints)
        print("ERROR: invalid scenario: both players are under check" \
                + " simultaneously")
        exit()
    game.set_turn(orig_turn) # Reset original player moving next
    if ((nchk0 > 0 and orig_turn == "b")
        or (nchk1 > 0 and orig_turn == "w")):
        if show_games: game.show(show_attack_footprints)
        print("ERROR: invalid scenario. Player "+orig_turn+" will move" \
                + " next -> player "+game.get_next_turn() \
                + " can't be in check")
        exit()
    if nchk0 > 2 or nchk1 > 2:
        if show_games: game.show(show_attack_footprints)
        print("ERROR: more than 2 checks simultaneously on ", end="")
        print(("w King (K0)" if nchk0 > 2 else "b King (K1)"))
        exit()
    # At this point, the Game setup was found to be valid
    ngame = 0
    print("Initial game configuration is valid:")
    game.show(False)
    if (max_moves == 0): exit()

    #print("Exploring combinations of moves...\n")
    smateinx = "Mate-in-" + str(max_moves)
    if stop_at_1st_find:
        print("Searching for 1st " + smateinx + " solution", end="")
    else:
        print("Searching for ALL " + smateinx + " solutions", end="")
    print(" for", input_file, "...")

    game.set_num(-1)
    if iterative:
        evaluate_iteratively(game)
    else:
        evaluate_recursively(None, game, 0)

    show_final_summary(game)

if __name__ == '__main__':
    mateinx_solver(sys.argv[1:])
