#!/usr/bin/env python
#---*----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8
"""
mateinx.py
author: Raul Saavedra ( raul.saavedra@gmail.com )
date  : 2022.11.18
"""

import sys
import string
import re
import json
import copy
import hashlib
import numpy as np
import time
#import zlib
from pathlib import Path

class GamesRecord:
    def __init__(self):
        self._dict = dict()

    def put(self, board_key, data):
        self._dict[board_key] = data

    def get(self, board_key):
        return self._dict.get(board_key, max_depth_p1)

    def keys(self):
        return self._dict.keys()

show_end_games = False
chatty = True
show_attack_footprints = False
recurse = False
max_depth = 3
max_depth_p1 = max_depth + 1
wins_per_depth = [0]*(max_depth_p1)
draws_per_depth = [0]*(max_depth_p1)
input_file = 'game-01.json'
ngame = 0
ngames_rev = 0
nrec_calls = 0
debug_show = False
games_seen_at_depth = GamesRecord()

ORD_CAP_A = ord('A')
ORD_A = ord('a')
ORD_1 = ord('1')
NOPAWN = "KQRNB"
QRNB = "QRNB"
EMPTY_BOARD = " "*64
ZIPSTR  = "     "
ZIPSTRL = len(ZIPSTR)
ZIPCHAR = "_"
RULER = "0-------1-------2-------3-------4-------5-------6-------7-------"

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

EKINGS=(EK0, EK1)
EPAWNS=(EP0, EP1)
EQUEENS=(EQ0, EQ1)
EKNIGHTS=(EN0, EN1)

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

def compress(orig):
    '''
    # A very simple "compression", replacing consecutive spaces
    # (ZIPSTR) with a special character ZIPCHAR
    s = ""
    cursor = 0
    ps = orig.find(ZIPSTR, cursor)
    while ps >= 0:
        s = s + orig[cursor:ps] + ZIPCHAR
        cursor = ps + ZIPSTRL
        ps = orig.find(ZIPSTR, cursor)
    s = s + orig[cursor:]
    return s
    '''
    #return zlib.compress(orig.encode())
    return orig

def test_compress(orig):
    print("\norig : '"+orig+"'")
    print("compr: '"+compress(orig)+"'")

class ChessGame:

    def __init__(self):
        self._num = 0
        self._status = ["OK", "OK", "OK", "EMPTY"]
        self._movep = 0     # moving player
        self._waitp = 1     # waiting player
        self._board = self._empty_board()
        self._npcs = [0, 0]
        self._nchks = [0, 0]
        self._pcs = [[], []]
        self._parent = None
        self._last_move = None
        self._attackfp = [self._no_attackfp(), self._no_attackfp()]
        self._key = ""

    def init_from_json(self, game_json):
        self._num = 0
        self._status = ["OK", "OK", "OK", "VALIDATING"]
        self._movep = 0
        self._waitp = 1
        self._board = self._empty_board()
        self._npcs = [0, 0]
        self._nchks = [0, 0]
        self._pcs = [[], []]
        self._parent = None
        self._last_move = None
        self._depth = 0
        self._key = ""
        self._attackfp = [self._no_attackfp(), self._no_attackfp()]
        self._set_board_from_json(game_json)
        self._gen_key()

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
        # Last move needs two board coordinates (origin and dest squares)
        # in order to be able to tell whether a pawn had moved 2 squares
        # as last move right before our input board setup
        c1 = self._parse_coords(lastmv_str[0:2])
        c2 = self._parse_coords(lastmv_str[2:])
        if c1 is None or c2 is None:
            self._status[2] = "ERROR: invalid last move '" \
                                + lastmv_str+"' (should be of the form 'cRcR')"
            return
        elmpc = self._read_board(c2[0], c2[1])
        if (elmpc == ' ' or PIECE_DECODE[elmpc][1:2] != str(self._waitp)):
            st = "ERROR: conflict between last move '"+lastmv_str \
                    + "' and existing pieces, or turn"
            self._status[2] = st
        # Possible to-do: validate that the move is compatible with the
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
        self._num = 0
        self._parent = None
        self._depth = 0
        self._nchks = [0, 0]
        turn = game_json.get('turn', "?").lower()
        self.set_turn("w" if (turn == "w" or turn == "?") else "b")
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

    def _gen_all_attack_footps(self):
        # All pieces now on board, generate their attack foot prints
        for player in range(2):
            for pxy in self._pcs[player]:
                epc = pxy[0]                # Encoded piece
                dpc = PIECE_DECODE[epc]     # Decoded piece
                self._gen_piece_attack_footp(player, dpc, pxy[1], pxy[2])

    def _gen_piece_attack_footp(self, player, dpc, i, j):
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
                # stop checking any further in this attacking direction
                if self._read_board(ii, jj) != " ": break

    def _read_board(self, i, j):
        index = i + j*8
        return self._board[index:index+1]

    def _sort_pieces(self, player):
        self._pcs[player].sort()

    def clone_for_knight_promotion():
        return child_game_2

    def init_from_parent_game(self, pgame, pmove, child_board, child_key):
        # Generate ChildGame's board from parent one + move
        self._status = ["OK", "OK", "OK", "EMPTY"]
        # For now keep the same moving player as from parent game
        self.set_turn(pgame.get_turn())
        self._parent = pgame
        self._num = -1 # -pgame._num
        self._depth = pgame._depth + 1
        self._last_move = pmove
        self._board = child_board
        self._key = child_key
        self._pcs = [[], []]
        # moving piece from old square at i0, j0
        oldsq = pmove[0]
        i0 = oldsq[0]
        j0 = oldsq[1]
        # to new square at i1, j1
        newsq = pmove[1]
        i1 = newsq[0]
        j1 = newsq[1]
        # moving piece
        empc = self._read_board(i1, j1)    # Encoded moved piece
        # Clone pieces for our soon moving player from parent game's
        # waiting player, except that one piece (if any) which might
        # have been in the destination square (such a piece would be
        # getting captured by this move)
        capture = 0
        for p in pgame._pcs[pgame._waitp]:
            #print(p)
            px = p[1]
            py = p[2]
            if px == i1 and py == j1:
                # The piece we had there in that square just got captured
                capture = 1
                continue
            new_p = [p[0], px, py]
            self._pcs[pgame._waitp].append(new_p)
        # Clone pieces for our soon waiting player from parent's game
        # moving player,
        promotion = False
        for p in pgame._pcs[pgame._movep]:
            px = p[1]
            py = p[2]
            if px == i0 and py == j0:
                # This is the moving piece. Use the piece encoded
                # in the new board, which will be different from the
                # original in the case of a pawn promotion
                new_p = [empc, i1, j1]
                if empc != p[0]:
                    promotion = True
            else:
                new_p = [p[0], px, py]
            #print ("Adding piece", new_p, "to child game")
            self._pcs[pgame._movep].append(new_p)
        self._npcs[pgame._movep] = pgame._npcs[pgame._movep]
        self._npcs[pgame._waitp] = pgame._npcs[pgame._waitp] - capture
        self._attackfp = [self._no_attackfp(), self._no_attackfp()]
        self._gen_all_attack_footps()
        if promotion:
            print("***** After game " + str(pgame.get_num()) \
                    + " a promotion into "+PIECE_DECODE[empc] \
                    + " took place at "+str(i1)+","+str(j1)+" *****")

    def get_parent_game(self):
        return self._parent

    def _empty_board(self):
        return EMPTY_BOARD

    def get_board(self):
        return self._board

    def _no_attackfp(self):
        return np.zeros([8,8])

    def _gen_new_board(self, oldboard, piece, idx_from, idx_to):
        newBoard = oldboard[0:idx_from] \
                    + " " \
                    + oldboard[idx_from+1:]
        newBoard = newBoard[0:idx_to] \
                    + piece \
                    + newBoard[idx_to+1:]
        return newBoard


    def simulate_move(self, m):
        ''' Returns a list of children boards given a move.
        Typically just 1 board inside, but 2 when promoting a pawn:
        one for promoting into queen, and one into knight.
        (Never promoting into rooks or bishops, since they are never
        preferable over a Queen.)
        '''
        ydest = m[1][1]
        index_old = m[0][0] + m[0][1]*8
        index_new = m[1][0] + ydest*8
        # Encoded moving piece
        empc = self._board[index_old:index_old+1]
        if empc in EPAWNS and (ydest == 0 or ydest == 7):
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
            return [ch_board_q, ch_board_n]
        else:
            # Just move the piece from old to new position
            ch_board = self._gen_new_board(
                            self._board,
                            empc,
                            index_old,
                            index_new)
            return [ch_board]

    def set_num(self, num, depth):
        self._num = num
        self._depth = depth

    def get_num(self):
        return self._num

    def get_depth(self):
        return self._depth

    def _gen_key(self):
        #self._key = compress(self.get_turn() + self._board)
        self._key = self.get_turn() + self._board

    def get_child_key(self, child_board):
        return self.get_next_turn() + child_board

    def get_key(self):
        return self._key

    #def _encode_piece(self, ptype, strplayer):
    #    return PIECE_ENCODE[ptype+strplayer]

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
            self._status[3] = "VALID"
            return "OK"
        self._status[3] = "INVALID"
        return ("Whites  : "+self._status[0] + "\n"
                + "Blacks  : "+self._status[1] + "\n"
                + "Gameplay: "+self._status[2] + "\n"
                + "Overall : "+self._status[3])

    def get_path_from_root(self):
        if self._parent is None:
            return (() if self._last_move is None else self._last_move)
        else:
            path = self._parent.get_path_from_root()
            path.append(self._last_move)
            return path

    def _get_pawn_checks(self, eking, kx, ky):
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

    def _get_long_checks(self, eking, kx, ky):
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

    def _get_knight_checks(self, eking, kx, ky):
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

    def get_all_checks(self):
        # Scan all attacks from the playing King's point of view
        #print("get_all_checks: running for game #", self._num, "turn", self.get_turn())
        king = self._pcs[self._movep][0]
        eking = king[0]
        kx = king[1]
        ky = king[2]
        nchks = (self._get_pawn_checks(eking, kx, ky)
                + self._get_long_checks(eking, kx, ky)
                + self._get_knight_checks(eking, kx, ky))
        self._nchks[self._movep] = nchks
        return nchks

    def _append_nonpawn_moves(self, moves, ptype, i, j):
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
                if (ptype == "K") and \
                    self._attackfp[self._waitp][ii][jj] > 0:
                    # Square is out of bounds for our king, skip
                    continue
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
                        # valid when capturing a 2-square moving enemy
                        # pawn that just moved next to ours. We have to
                        # identify this possibility here
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
                        if (self._last_move == ()
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
                        # indeed capture it
                        print("***** Detected pawn capturing " \
                                + "2-square moving pawn *****")
                newmove = ((i,j), (ii,jj))
                moves.append(newmove)

    def get_all_moves(self, nchecks):
        # Generate list of all valid moves to consider
        movable_pcs = []
        if nchecks < 2:
            # Not under double check, so consider non-king piece movements
            npieces = len(self._pcs[self._movep])
            for i in range(1,npieces,1):
                p = self._pcs[self._movep][i]
                key = p[0] + str(p[1]) + str(p[2])
                movable_pcs.append( p )
        # The king is always among the pieces to consider
        movable_pcs.append(self._pcs[self._movep][0])
        # Generate all valid moves for the movable pieces
        player_moves = []
        for p in movable_pcs:
            dp = PIECE_DECODE[p[0]]
            dpt = dp[0:1]
            i = p[1]
            j = p[2]
            if dpt == "p":
                self._append_pawn_moves(player_moves, dp, i, j)
            else:
                self._append_nonpawn_moves(player_moves, dpt, i, j)
        return player_moves

    def show(self):
        nums = \
            "        0      1      2      3      4      5      6      7"
        letters = \
            "        a      b      c      d      e      f      g      h"
        horiz = \
            "    +------+------+------+------+------+------+------+------+"
        print("\nGame #:", self._num, "(depth "+str(self._depth)+")")
        print(letters)
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
                if show_attack_footprints:
                    print("|", end="")
                    wattacks = int(self._attackfp[0][i][7-j])
                    if wattacks != 0:
                        print(f"{wattacks:02d}", end="")
                    else:
                        print("  ", end="")
                    print("  ", end="")
                    battacks = int(self._attackfp[1][i][7-j])
                    if battacks != 0:
                        print(f"{battacks:02d}", end="")
                    else:
                        print("  ", end="")
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
        print("\tTo play: "+self.get_turn()+"    ", end="")
        print("Checked: w="+str(self._nchks[0])+" b=" \
                + str(self._nchks[1]) + "     ", end="")
        print("Move history:\n\t", end="")
        print(self.get_path_from_root())


BAR = '='*48

def starting_banner():
     print("\n"+BAR)
     print('|      mateinx.py                              |')
     print('|      By Raul Saavedra F., 2022-Nov-18        |');
     print(BAR)

def load_game_from_json():
    with open(input_file, 'r') as f:
        game_json = json.load(f)
    g = game_json['chess-game']
    if chatty:
        print("Starting game (.json input):")
        print(json.dumps(game_json, indent=4)+"\n")
    return g

def evaluate_recursively(parent, parent_move, game, depth):
    global ngame
    global games_seen_at_depth
    global ngames_rev
    global nrec_calls
    global debug_show
    nrec_calls += 1
    if depth > max_depth:
        return "Too deep"
    game.set_num(ngame, depth)
    ngame += 1
    if chatty and ngame % 2000 == 0:
        print("Games Processed:", ngame)
    gkey = game.get_key()
    games_seen_at_depth.put(gkey, depth)
    nchks = game.get_all_checks()
    moves = game.get_all_moves(nchks)
    if debug_show:
        game.show()
        print("depth=", depth, "Parent move:", parent_move)
        #print(game.get_board())
        #print("Moves:\n", moves)
        #exit()
    ve = verify(game, moves)
    if ve != "ok":
        return "Done here"
    if depth >= max_depth:
        return "Deep enough"
    next_depth = depth + 1
    nvalid_moves = 0
    for m in moves:
        # Simulate move and check if resulting board has already been seen
        child_boards = game.simulate_move(m)
        for ch_brd in child_boards:
            ch_key = game.get_child_key(ch_brd)
            d_last_seen = games_seen_at_depth.get(ch_key)
            if d_last_seen <= depth:
                ngames_rev += 1
                if chatty and ngames_rev % 10000 == 0:
                    print("Games Revisited:", ngames_rev)
                continue
            # First time seeing this game, or we might have seen this game
            # before, but if so, it was at a deeper depth. So we need to
            # explore it further down from up here.
            # To-do: This can be optimized further if that last time
            # seen wasn't at the max depth.

            # Generate new child game and do apply move to explore further
            child_game = ChessGame()
            child_game.init_from_parent_game(game, m, ch_brd, ch_key)
            nchks_in_child = child_game.get_all_checks()
            if nchks_in_child > 0:
                # Our King is left in check with this move: invalid
                # We can break from the inner for already since it has a
                # second loop only when promoting a pawn, but regardless
                # of Queen or Knight, if the first promotion is invalid
                # the second will be as well
                break
            nvalid_moves += 1
            child_game.flip_turn()
            evaluate_recursively(game, m, child_game, next_depth)
    if nvalid_moves == 0:
        result = verify(game, [])
    return "Subtree processed"

def verify(game, moves):
    global ngame
    global wins_per_depth
    global draws_per_depth
    global show_end_games
    depth = game.get_depth()
    if game.get_npcs(0) + game.get_npcs(1) == 2:
        draws_per_depth[depth] += 1
        if show_end_games:
            game.show()
        print("DRAW (only both Kings remain) found at game #",
                ngame, "depth", depth)
        return "GAME OVER: DRAW"
    if moves == []:
        nchks = game.get_num_checks(game.get_mover())
        if nchks > 0:
            if nchks > 2:
                error_msg = "ERROR: invalid scenario: more than two" \
                            + "checks simultaneously on "+game.get_turn()
                print(error_msg)
                exit()
            # No moves and the player to move is under Check ->
            #   Game over: LOST the game
            winner = game.get_next_turn()
            wins_per_depth[depth] += 1
            print("WIN for", winner, "found at game #",
                    ngame, "depth", depth)
            return "GAME OVER: Player", winner, "WINS!"
        else:
            # No moves and not under check -> Game over: DRAW
            draws_per_depth[depth] += 1
            if show_end_games:
                game.show()
            print("DRAW found at game #", ngame, "depth", depth)
            return "GAME OVER: DRAW"
    return "ok"

def process_options(argv):
    global input_file
    global recurse
    global show_attack_footprints
    global chatty
    global max_depth, max_depth_p1, wins_per_depth, draws_per_depth
    for opt in argv:
        if opt == "-h":
            # Display help
            with open('mateinx.txt') as help:
                for line in help:
                    print(line.rstrip())
            exit()
        if opt == "-r":
            # Do recurse to find solution
            recurse = True
            continue
        if opt == "-a":
            # Do show Attack Footprints
            show_attack_footprints = True
            continue
        if opt == "-q":
            # Run in quiet mode
            chatty = False
            continue
        if opt[0:2] == "-d":
            # Set maximum depth to explore
            n=opt[2:]
            if n.isdecimal():
                max_depth = int(n)
                max_depth_p1 = max_depth + 1
                wins_per_depth = [0]*(max_depth_p1)
                draws_per_depth = [0]*(max_depth_p1)
            else:
                print("Invalid max depth parameter:", n)
            print("Using", max_depth, "as maximum depth")
            continue
        if not opt.startswith("-"):
            # This should be the file name (.json) to use as input
            fname = opt
            vpath = Path(fname)
            if vpath.is_file():
                input_file = fname
                if chatty: print("Using '"+input_file+"' as input file")
            else:
                print("ERROR: file '"+fname+"' not found, exiting")
                exit(-2)
            continue
        print("ERROR: "+opt+" is not an option, use -h for usage details")
        exit(-1)

def mateinx_solver(argv):
    global ngame
    global chatty
    global nrec_calls
    global ngames_rev
    starting_banner()
    process_options(argv)
    start = load_game_from_json()
    game = ChessGame()
    game.init_from_json(start)
    vst = game.get_status()
    if vst != "OK":
        print(vst)
        exit()
    # Aditional validations before starting recursive calls
    orig_turn = game.get_turn()
    game.set_turn("w")
    nchk0 = game.get_all_checks()
    vst = game.get_status()
    if vst != "OK":
        game.show()
        print(vst)
        exit()
    game.set_turn("b")
    nchk1 = game.get_all_checks()
    vst = game.get_status()
    if vst != "OK":
        game.show()
        print(vst)
        exit()
    if nchk0 > 0 and nchk1 > 0:
        game.show()
        print("ERROR: invalid scenario: both players are under check" \
                + " simultaneously")
        exit()
    game.set_turn(orig_turn) # Reset original player moving next
    if ((nchk0 > 0 and orig_turn == "b")
        or (nchk1 > 0 and orig_turn == "w")):
        game.show()
        print("ERROR: invalid scenario. Player "+orig_turn+" will move" \
                + " next -> player "+game.get_next_turn() \
                + " can't be in check")
        exit()
    if nchk0 > 2 or nchk1 >2:
        game.show()
        print("ERROR: more than 2 checks simultaneously on", \
                "w" if nchk0 > 2 else "b", "King")
        exit()
    # At this point, the Game setup was found to be valid
    ngame = 0
    if chatty:
        print("Initial Game configuration is valid:")
        game.show()
        print(BAR)
    if recurse:
        evaluate_recursively(None, (), game, 0)
    end_time = time.time()
    print("\nTotal recursive calls:", nrec_calls)
    print("Total games processed:", ngame)
    print("Total games revisited:", ngames_rev)
    print("Win-in-X  games found per depth:", wins_per_depth)
    print("Draw-in-X games found per depth:", draws_per_depth)

if __name__ == '__main__':
    mateinx_solver(sys.argv[1:])
