#!/usr/bin/env python
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
import zlib
from pathlib import Path

class GamesRecord:
    def __init__(self):
        self.__dict = dict()

    def hasBoard(self, board_key):
        bkey = self.__getKey(board_key)
        if bkey in self.__dict: return True
        return False

    def put(self, board_key, node):
        bkey = self.__getKey(board_key)
        self.__dict[bkey] = node

    def get(self, board_key):
        bkey = self.__getKey(board_key)
        return self.__dict.get(bkey, max_depth)

    def __getKey(self, board_key):
        #kobj = hashlib.md5(board_key.encode('utf-8'))
        #return "k"+str(kobj.hexdigest())
        return "k"+board_key

    def keys(self):
        return self.__dict.keys()

showEndGames = False
chatty = True
show_attack_footprints=False
recurse=False
max_depth=4
wins_per_depth = [0]*(max_depth+1)
draws_per_depth = [0]*(max_depth+1)
input_file = 'game-01.json'
nGame = 0
nGamesRevisited = 0
nRecCalls = 0
debugShow = False
gamesSeenAtDepth = GamesRecord()
ORD_A = ord('a')
ORD_1 = ord('1')
NOPAWN="KQRBN"
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

KINGS=(EK0, EK1)

# Pawn attacks from perspective of an attacked king
PATTACKS = {
            EK0: (EP1, ((-1, 1), (1, 1))),
            EK1: (EP0, ((-1, -1), (1, -1))),
            }

PAWN_MOVES = {          # Conditional moves for pawns
    # White pawns
    "p0":   (
            ((-1,1),),   # Only when capturing
            ((0,1),),    # Only when no piece in destination
            ((0,2),),    # Only when at their starting row, and no piece in dest
            ((1,1),)     # Only when capturing
            ),
    # Black pawns
    "p1":   (
            ((-1,-1),),  # Only when capturing
            ((0,-1),),   # Only when no piece in destination
            ((0,-2),),   # Only when at their starting row, and no piece in dest
            ((1,-1),)    # Only when capturing
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
For each piece type, the valid attacks are stored as a list of lists.
Each sublist explores a given direction from the piece's position
outwards. Can therefore be scanned until a piece on the board is found
(blocking or getting the attack), then jump to next direction sublist
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
            ((-1,0), (-2,0), (-3,0), (-4,0), (-5,0), (-6,0), (-7,0)),
            ((1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0)),
            # Diag NW-SE
            ((-1,1), (-2,2), (-3,3), (-4,4), (-5,5), (-6,6), (-7,7)),
            ((1,-1), (2,-2), (3,-3), (4,-4), (5,-5), (6,-6), (7,-7)),
            # Diag SW-NE
            ((-1,-1), (-2,-2), (-3,-3), (-4,-4), (-5,-5), (-6,-6), (-7,-7)),
            ((1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)),
            ),
    # Rooks
    "R":    (
            # Vert N-S
            ((0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7)),
            ((0,-1), (0,-2), (0,-3), (0,-4), (0,-5), (0,-6), (0,-7)),
            # Horiz L-R
            ((-1,0), (-2,0), (-3,0), (-4,0), (-5,0), (-6,0), (-7,0)),
            ((1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0)),
            ),
    # Bishops
    "B":    (
            # Diag NW-SE
            ((-1,1), (-2,2), (-3,3), (-4,4), (-5,5), (-6,6), (-7,7)),
            ((1,-1), (2,-2), (3,-3), (4,-4), (5,-5), (6,-6), (7,-7)),
            # Diag SW-NE
            ((-1,-1), (-2,-2), (-3,-3), (-4,-4), (-5,-5), (-6,-6), (-7,-7)),
            ((1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7)),
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

def compress(orig):
    '''
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
    return orig

def test_compress(orig):
    print("\norig : '"+orig+"'")
    print("compr: '"+compress(orig)+"'")

class ChessGame:

    def __init__(self):
        self.__num = 0
        self.__status = ["OK", "OK", "OK", "EMPTY"]
        self.__turn = "w"
        self.__nextTurn = "b"
        self.__movep = 0
        self.__waitp = 1
        self.__smovep = "0"
        self.__swaitp = "1"
        self.__board = self.__empty_board()
        self.__npcs = [0, 0]
        self.__nchks = [0, 0]
        self.__pcs = [[], []]
        self.__parent = None
        self.__lastMove = None
        self.__attackfp = [self.__no_attackfp(), self.__no_attackfp()]
        self.__key = ""

    def initFromJson(self, game_json):
        self.__num = 0
        self.__status = ["OK", "OK", "OK", "VALIDATING"]
        self.__turn = "w"
        self.__nextTurn = "b"
        self.__movep = 0   # moving player
        self.__waitp = 1   # waiting player
        self.__smovep = "0"
        self.__swaitp = "1"
        self.__board = self.__empty_board()
        self.__npcs = [0, 0]
        self.__nchks = [0, 0]
        self.__pcs = [[], []]
        self.__parent = None
        self.__lastMove = None
        self.__depth = 0
        self.__key = ""
        self.__attackfp = [self.__no_attackfp(), self.__no_attackfp()]
        self.__set_board_from_json(game_json)
        self.__gen_key()

    def __set_piece_from_json(self, player, piece, i, j):
        epiece = self.__encode_piece(player, piece)
        index = i + j*8
        self.__board = self.__board[0:index] + epiece + self.__board[index+1:]
        self.__pcs[player].append([epiece, i, j])
        self.__npcs[player] = self.__npcs[player] + 1

    def __set_board_from_json(self, game_json):
        self.__num = 0
        self.__parent = None
        self.__depth = 0
        self.__nchks = [0, 0]
        self.__lastMove = game_json.get('lastMove', "")
        turn = game_json.get('turn', "?").lower()
        self.__turn = "w" if turn=="w" or turn=="?" else "b"
        moving_player = 0 if self.__turn=="w" else 1
        moving_king = KINGS[moving_player]
        for player in range(2):
            color = "w" if player==0 else "b"
            pieces = game_json.get(color+"pcs", [])
            x = 0
            y = 0
            counts = {}
            counts["p"] = 0
            promoted = 0
            strplayer = str(player)
            for w in pieces:
                piece = w[0:1]
                if (piece>='a' and piece<='h'):
                    # Here's a pawn
                    x = w[0:1]
                    y = w[1:2]
                    piece = "p"
                    counts["p"] = counts["p"] + 1
                else:
                    if piece in NOPAWN:
                         # Valid non-pawn piece
                         counts[piece] = counts.get(piece, 0) + 1
                         if piece != "K":
                             # Count any promoted pieces
                             promoted = promoted + (1 if (counts[piece] > (1 if piece=="Q" else 2)) else 0)
                    else:
                        self.__status[player] = "ERROR: invalid piece "+piece+" in "+w
                        return
                    x = w[1:2]
                    y = w[2:3]
                if (x < 'a' or x > 'h' or y < '1' or y > '8'):
                    self.__status[player] = "ERROR: invalid position ({0},{1}) in {2}".format(x,y,w)
                    return
                #x,y are text "a"-"h","1"-"8" coordinates
                #i,j are the corresponding 0-7 numeric coordinates
                i = ord(x) - ORD_A
                j = int(y) - 1
                if self.__read_board(i, j) != " ":
                    self.__status[player] = "ERROR: two pieces detected in same position {0}{1}".format(x,y)
                    return
                self.__set_piece_from_json(player, piece+strplayer, i, j)
            if counts.get("K", 0) != 1:
                self.__status[player] = "ERROR: {0} King pieces for {1} player".format(counts.get("K", 0), color)
                return
            if counts["p"] > 8:
                self.__status[player] = "ERROR: {0} pawns for {1} player".format(counts["p"], color)
                return
            if promoted > 8 - counts["p"]:
                self.__status[player] = "ERROR: {0} pawns + {1} promoted pieces, too many for ".format(counts["p"], promoted)+color+" player"
                return
            self.__sort_pieces(player)
        self.__gen_attack_footprints()

    def __gen_attack_footprints(self):
        # All pieces now on board, generate their attack foot prints
        for player in range(2):
            for pxy in self.__pcs[player]:
                epc = pxy[0]                # Encoded piece
                dpc = PIECE_DECODE[epc]     # Decoded piece
                self.__update_attack_footps(player, dpc, pxy[1], pxy[2])

    def __update_attack_footps(self, player, dpc, i, j):
        #print("Updating attack footprint for player", str(player), ", piece", dpc, "@", str(i),",",str(j),"delta=", delta)
        vp = dpc if dpc[0:1]=="p" else dpc[0:1]
        vmoves = ATTACK_MOVES.get(vp, [])
        #print("vp:",vp, "moves:", vmoves)
        afp = self.__attackfp[player]
        for movedir in vmoves:
            for m in movedir:
                #print("Processing",m)
                ii = i + m[0]
                if (ii<0 or ii>7): break
                jj = j + m[1]
                if (jj<0 or jj>7): break
                #print("\t Marking "+str(ii)+", "+str(jj)+" under "+str(player)+" attack")
                nattacks = afp[ii][jj]
                afp[ii][jj] = nattacks + 1
                # Here check if board has a piece here, and if so
                # stop checking any further in this attacking direction
                if self.__read_board(ii, jj) != " ": break

    def __read_board(self, i, j):
        index = i + j*8
        return self.__board[index:index+1]

    def __sort_pieces(self, player):
        self.__pcs[player].sort()

    def initFromParentGame(self, pgame, pmove, childBoard, childKey):
        # Generate ChildGame's board from parent one + move
        #print("Running __init__ from Parent game with move", pmove)
        self.__status = ["OK", "OK", "OK", "EMPTY"]
        #self.setTurn(childKey[0:1])
        self.setTurn(pgame.__turn) # At first keep the same moving player as from parent game
        self.__parent = pgame
        self.__depth = pgame.__depth+1
        self.__lastMove = pmove
        #print("\nchildBoard:", childBoard)
        #print("childKey  :", childKey)
        self.__board = childBoard
        self.__pcs = [[], []]
        #self.__attackfp = np.copy(pgame.__attackfp)
        # from square
        fromsq = pmove[0]
        i0 = fromsq[0]
        j0 = fromsq[1]
        # to square
        destsq = pmove[1]
        i1 = destsq[0]
        j1 = destsq[1]
        # moving piece
        empc = self.__read_board(i1, j1)    # Encoded moved piece
        if (empc == " "):
            self.show()
            print("         "+RULER)
            print("Parent: '"+pgame.getBoard()+"'")
            print("Child : '"+self.getBoard()+"'")
            print("ERROR: This should never happen. The previously moved piece should be there")
            exit()

        pcpc = pgame.__read_board(i1, j1)
        if pcpc == pgame.__pcs[pgame.__waitp][0][0]:
            self.show()
            print("         "+RULER)
            print("Parent: '"+pgame.getBoard()+"'")
            print("P.move:", pmove)
            print("Child : '"+self.getBoard()+"'")
            print("ERROR: This should never happen: a King getting captured?")
            exit()

        dmpc = PIECE_DECODE[empc]           # Decoded moved piece
        # Clone pieces for our soon moving player from parent game's waiting player
        # except that one piece (if any) which might have been in the destination square
        # (which would be getting captured by this move)
        capture = 0
        for p in pgame.__pcs[pgame.__waitp]:
            #print(p)
            px = p[1]
            py = p[2]
            if (px==i1 and py==j1):
                # The piece we had there in that square just got captured
                capture = 1
                continue
            new_p = [p[0], px, py]
            self.__pcs[pgame.__waitp].append(new_p)
        # Clone pieces for our soon waiting player from parent's game moving player,
        for p in pgame.__pcs[pgame.__movep]:
            px = p[1]
            py = p[2]
            if (px==i0 and py==j0):
                # This is the moving piece, update coordinates with move's destination
                new_p = [p[0], i1, j1]
            else:
                new_p = [p[0], px, py]
            self.__pcs[pgame.__movep].append(new_p)
        self.__npcs[pgame.__movep] = pgame.__npcs[pgame.__movep]
        self.__npcs[pgame.__waitp] = pgame.__npcs[pgame.__waitp] - capture
        self.__attackfp = [self.__no_attackfp(), self.__no_attackfp()]
        self.__gen_attack_footprints()
        #self.__gen_key()
        self.__key = childKey

    def getParentGame(self):
        return self.__parent

    def __empty_board(self):
        return EMPTY_BOARD

    def getBoard(self):
        return self.__board

    def __no_attackfp(self):
        return np.zeros([8,8])

    def simulateMove(self, m):
        #print(m)
        index_from = m[0][0] + m[0][1]*8
        index_to = m[1][0] + m[1][1]*8
        empc = self.__board[index_from:index_from+1]
        newBoard = self.__board[0:index_from] + " " + self.__board[index_from+1:]
        newBoard = newBoard[0:index_to] + empc + newBoard[index_to+1:]
        #if (debugShow):
        #    print(self.__board)
        #    print(newBoard)
        return (newBoard, compress(self.__nextTurn + newBoard))

    def setNum(self, num, depth):
        self.__num = num
        self.__depth = depth

    def getNum(self):
        return self.__num

    def getDepth(self):
        return self.__depth

    def __gen_key(self):
        #self.__key = self.__turn+self.__board
        #self.__key = zlib.compress((self.__turn+self.__board).encode())
        self.__key = compress(self.__turn + self.__board)

    def getKey(self):
        return self.__key
        #return zlib.decompress(self.__key).decode()

    def dumpAttackFps(self):
        print(self.__attackfp[0])
        print(self.__attackfp[1])

    def isAttacked(self, i, j):
        index = i + j*8
        return "x" == self.__attacks[index:index+1]

    def __encode_piece(self, player, piece):
        return PIECE_ENCODE[piece]

    def __decode_piece_from_board(self, i, j):
        p = self.__read_board(i,j)
        if p == " ": return "  "
        return PIECE_DECODE[p]

    def setTurn(self, turn):
        if turn == "b":
            self.setMovingPlayer(1)
        else:
            self.setMovingPlayer(0)

    def setMovingPlayer(self, movep):
        if movep == 1:
            self.__turn     = "b"
            self.__nextTurn = "w"
            self.__movep  = 1     # moving player
            self.__smovep = "1"
            self.__waitp  = 0     # waiting player
            self.__swaitp = "0"
        else:
            self.__turn     = "w"
            self.__nextTurn = "b"
            self.__movep  = 0
            self.__smovep = "0"
            self.__waitp  = 1
            self.__swaitp = "1"

    def getMovingPlayer(self):
        return self.__movep

    def getWaitingPlayer(self):
        return self.__waitp

    def flipTurn(self):
        if self.__movep == 0:
            self.setMovingPlayer(1)
        else:
            self.setMovingPlayer(0)

    def getTurn(self):
        return self.__turn

    def getNextTurn(self):
        return self.__nextTurn

    def getNpcs(self, player):
        if (player < 0 or player > 1): return 0
        return self.__npcs[player]

    def getNumChecks(self, player):
        if (player < 0 or player > 1): return 0
        return self.__nchks[player]

    def getStatus(self):
        if (self.__status[0]=="OK" and self.__status[1]=="OK" and self.__status[2]=="OK"):
            self.__status[3] = "VALID"
            return "OK"
        self.__status[3] = "INVALID"
        return  "Whites  : "+self.__status[0]+"\n" \
                "Blacks  : "+self.__status[1]+"\n" \
                "Gameplay: "+self.__status[2]
    '''
    def printPathFromRoot(self):
        if (self.__parent == None):
            print("\tStart (", ("-" if self.__lastMove==None else self.__lastMove), ")")
        else:
            self.__parent.printPathFromRoot()
            print("\t", end="")
            print(self.__lastMove)
    '''

    def getPathFromRoot(self):
        if (self.__parent == None):
            return ([] if self.__lastMove==None else self.__lastMove)
        else:
            path = self.__parent.getPathFromRoot()
            path.append(self.__lastMove)
            return path

    def updateAttackFootps(self, processMoves):
        # Scan all attacks from the playing King's point of view
        king = self.__pcs[self.__movep][0]
        eking = king[0]
        if eking != EK0 and eking != EK1:
            print("Last move was:", self.__lastMove)
            print("Last board:")
            self.show()
            print("ERROR: The piece that should be the king is now", king, "("+PIECE_DECODE[eking]+")", \
                  "This should never happen. The program should have detected the", \
                  "end of game before. Exiting.")
            exit()
        dking = PIECE_DECODE[eking]
        #print("\nScanning attacks for player", self.__smovep, "King is", king, "(", dking, "), GenMoves:", processMoves)
        kx = king[1]
        ky = king[2]
        #print ("King's position: ", end="")
        #print ([dking, kx, ky])
        pinnedPcs = {}
        # Scanning possible pawn attacks
        pattacks = PATTACKS[king[0]]
        epawn = pattacks[0]
        la = pattacks[1]
        nchks = 0
        for pos in la:
            x = kx + pos[0]
            y = ky + pos[1]
            if (x >= 0 and x < 8 and y >= 0 and y < 8):
                square = self.__read_board(x, y)
                if square == epawn:
                    # Pawn checking this king
                    #print("p"+self.__swaitp+" at "+chr(ORD_A+x)+","+chr(ORD_1+y)+" CHECKING "+dking)
                    nchks = 1
                    # We can break from this loop already, not
                    # possible to have more than 1 enemy pawn checking us
                    break
        # Scanning all linear attacks to find all pinned pieces and checks
        for adir, ainfo in LATTACKS.items():
            xdelta = ainfo[0]
            ydelta = ainfo[1]
            apieces = ainfo[2]
            scanx = kx + xdelta
            scany = ky + ydelta
            ourpiece = []
            First = True
            while (scanx >= 0 and scanx < 8 and scany >= 0 and scany < 8):
                square = self.__read_board(scanx, scany)
                if (square != " "):
                    piece = PIECE_DECODE[square]
                    #print("\tPiece "+piece+" found in linear-scan at "+str(scanx)+","+str(scany))
                    if piece[1:2]==self.__swaitp:
                        ptype = piece[0:1]
                        # It's enemy
                        if ptype in apieces:
                            if First:
                                #print(piece+" at "+chr(ORD_A+scanx)+","+chr(ORD_1+scany)+" CHECKING "+dking)
                                nchks = nchks + 1
                            else:
                                # Our piece we found first is pinned by this enemy piece
                                #print(piece+" at "+chr(ORD_A+scanx)+","+chr(ORD_1+scany)+" PINNING ", end="")
                                #print(PIECE_DECODE[ourpiece[0]])
                                pinnedPcs[ourpiece]="1"
                        #else: Enemy piece there, but it does not attack our king in this direction,
                        #      so we can move on to the next scan direction
                        break
                    else:
                        if not First: break
                        First = False
                        ourpiece = square+str(scanx)+str(scany)
                scanx = scanx + xdelta
                scany = scany + ydelta
        # Scanning all knight attacks
        lnpos = NATTACKS
        #print(lnpos)
        for pos in lnpos:
            #print(pos)
            scanx = kx + pos[0]
            scany = ky + pos[1]
            if (scanx >= 0 and scanx < 8 and scany >= 0 and scany < 8):
                square = self.__read_board(scanx, scany)
                if (square != " "):
                    piece = PIECE_DECODE[square]
                    if piece[0:1]=="N" and piece[1:2]==self.__swaitp:
                        #print(piece+" at "+chr(ORD_A+scanx)+","+chr(ORD_1+scany)+" CHECKING "+dking)
                        nchks = nchks + 1
        self.__nchks[self.__movep] = nchks
        if (nchks > 0):
            #print("King "+dking+" attacked by "+str(nchks)+" check(s)")
            if (nchks > 2):
                self.__status[2] = "ERROR: invalid scenario with 3 or more simultaneous checks on "+dking
                self.__status[3] = "INVALID"
                return []

        if not processMoves: return []

        # Generate list of valid moves to consider
        movablePcs = []
        if (nchks < 2):
            # Not under a double check, so consider non-king piece movements
            npieces = len(self.__pcs[self.__movep])
            for i in range(1,npieces,1):
                p = self.__pcs[self.__movep][i]
                key = p[0] + str(p[1]) + str(p[2])
                movablePcs.append( p )
        # The king is always among the pieces to consider
        movablePcs.append( self.__pcs[self.__movep][0] )
        #print("Movable pieces:", movablePcs)
        # Generate all valid moves for the movable pieces
        player_moves = []
        for p in movablePcs:
            dp = PIECE_DECODE[p[0]]
            ptype = dp[0:1]
            i = p[1]
            j = p[2]
            #print("Generating valid moves for", p, "("+dp+") at ", i, ",", j)
            if ptype == "p":
                # Pawns require very special movement considerations
                vmoves = PAWN_MOVES.get(dp)
                for movedir in vmoves:
                    for m in movedir:
                        ii = i + m[0]
                        if (ii<0 or ii>7): break
                        jj = j + m[1]
                        if (jj<0 or jj>7): break
                        square = self.__read_board(ii, jj)
                        if m[0] == 0:
                            # Only move vertically if path to destination square is free
                            if square != " ":
                                continue
                            m1 = m[1]
                            #print("j is "+str(j)+" player is "+splayer+" m[1] is "+str(m[1]))
                            # If trying to move 2-squares only valid if from the starting raw
                            if m1 == 2:
                                if (j!=1 and self.__movep==0):
                                    # Our pawn is not in its starting raw so it can't do a 2-step move
                                    continue
                                if self.__read_board(ii, j+1) != " ":
                                    # Path is not clear for the pawn to move 2 sq
                                    continue
                            elif m1 == -2:
                                if j!=6 and self.__movep==1:
                                    continue
                                if self.__read_board(ii, j-1) != " ":
                                    # Path is not free for the pawn to move 2 sq
                                    continue
                        else:
                            # Moving diagonally
                            if square != " ":
                                # The square is occupied
                                if PIECE_DECODE[square][1:2] == self.__smovep:
                                    # A piece of ours is in that square, so skip this move
                                    continue
                            else:
                                # Moving diagonally into an empty square is only valid when
                                # capturing a 2-square moving enemy pawn that just moved next
                                # to ours. We have to identify this possibility here
                                if (jj!=5 and self.__movep==0) or (jj!=2 and self.__movep==1):
                                    # Our pawn is not in the right raw to be able to capture
                                    # a 2-moving pawn
                                    continue
                                squareAdj = self.__read_board(ii, j)
                                if squareAdj == " ":
                                    # The square next to our pawn is free
                                    continue
                                if (PIECE_DECODE[squareAdj] != "p"+self.__swaitp):
                                    # There is a piece there, but it's not an enemy pawn
                                    continue
                                # Here our pawn was in the right raw, and next to it there
                                # is an enemy pawn!
                                #print("Generating moves: p"+self.__smovep+" possibly capturing a 2-square enemy pawn!!!")
                                if (self.__lastMove==[] or self.__lastMove[1]!=ii or self.__lastMove[2]!=j):
                                    # Last move was not made by that pawn
                                    continue
                                # This enemy pawn actually made the very last move
                                epoy = self.__lastMove[0][2]
                                if ((enemy==1 and epoy!=6) or (enemy==0 and epoy!=1)):
                                    # But it was not a 2-square pawn move
                                    continue
                                # If we reached this point, we identified the case in which
                                # last move was that enemy pawn making its first move, and it
                                # was a 2-square move, and our pawn can capture it
                                #print("Generating moves: p"+self.__smovep+" CAPTURING a 2-square enemy pawn!!!!")
                        newmove = ((i,j), (ii,jj))
                        #print("Adding pawn move:", newmove)
                        player_moves.append( newmove )
            else:
                # Non-pawn piece
                vmoves = ATTACK_MOVES.get(dp[0:1])
                for movedir in vmoves:
                    for m in movedir:
                        ii = i + m[0]
                        if (ii<0 or ii>7): break
                        jj = j + m[1]
                        if (jj<0 or jj>7): break
                        #print("Move possibility:", m)
                        square = self.__read_board(ii, jj)
                        if square != " ":
                            posWhiteQueen = self.getBoard().find("B",0)
                            #if (posWhiteQueen==56):
                            #    print("square", square, "Decoded square", PIECE_DECODE[square], "Moving player", self.__smovep)
                            if PIECE_DECODE[square][1:2] == self.__smovep:
                                # A piece of ours in that square, move on to next attack direction
                                break
                            #if (posWhiteQueen==56):
                            #    print("Generating moves:", dp,"at",chr(ORD_A+i)+","+chr(ORD_1+j),"can CAPTURE",PIECE_DECODE[square])
                        if (ptype=="K") and self.__attackfp[self.__waitp][ii][jj] > 0:
                            # Square is out of bounds for our king, skip
                            continue
                        # Otherwise add the move as valid
                        newmove = ((i,j), (ii,jj))
                        #print("Adding non-pawn move:", newmove)
                        player_moves.append( newmove )
                        if square != " ":
                            # Destination square is occupied, no point exploring this moving direction any further
                            break
        #print(player_moves)
        #exit()
        return player_moves

    def applyMove(self, player, move):
        return childGame

    def show(self):
        nums   ="        0      1      2      3      4      5      6      7"
        letters="        a      b      c      d      e      f      g      h"
        horiz=  "    +------+------+------+------+------+------+------+------+"
        print("\nGame #:", self.__num, "(depth "+str(self.__depth)+")")
        print(letters)
        for j in range(8):
            print(horiz)
            print("    ", end="")
            whitesq = (j % 2 == 0)
            for i in range(8):
                if whitesq:
                    print("|      ", end="")
                else:
                    #print("|///\\\\\\", end="")
                    print("|######", end="")
                whitesq = not whitesq
            print("|")
            print("  {0} ".format(8-j), end="")
            for i in range(8):
                piece = self.__decode_piece_from_board(i, 7-j)
                if whitesq:
                    print("|  "+piece+"  ", end="")
                else:
                    print("|[ "+piece+" ]", end="")
                whitesq = not whitesq
            print("| {0}".format(7-j))
            print("    ", end="")
            for i in range(8):
                if (show_attack_footprints):
                    print("|", end="")
                    wattacks = int(self.__attackfp[0][i][7-j])
                    if (wattacks != 0):
                        print(f"{wattacks:02d}", end="")
                    else:
                        print("  ", end="")
                    print("  ", end="")
                    battacks = int(self.__attackfp[1][i][7-j])
                    if (battacks != 0):
                        print(f"{battacks:02d}", end="")
                    else:
                        print("  ", end="")
                else:
                    if whitesq:
                        print("|      ", end="")
                    else:
                        print("|\\\\\\///", end="")
                #print(f"{self.__attackfp[0][i][j]:02d}", end="")
                #print("  {:2d}".format(self.__attackfp[1][i][j]), end="")
                whitesq = not whitesq
            print("|")
        print(horiz)
        print(nums)
        print(letters)
        print("\tTo play: "+self.getTurn()+"    ", end="")
        print("Checks: w="+str(self.__nchks[0])+" b="+str(self.__nchks[1])+"      ", end="")
        print("Move history:\n\t", end="")
        print(self.getPathFromRoot())
        #print("wpcs (", self.__npcs[0], "):", self.__pcs[0])
        #print("bpcs (", self.__npcs[1], "):", self.__pcs[1])
        #print("0-------1-------2-------3-------4-------5-------6-------7-------")
        #print(self.__board)

BAR = '='*48

def starting_banner():
     print(BAR)
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
    global nGame
    global gamesSeenAtDepth
    global nGamesRevisited
    global nRecCalls
    global debugShow
    nRecCalls = nRecCalls + 1
    #if (depth > max_depth):
    #    return "Too deep"
    nGame += 1
    game.setNum(nGame, depth)
    if chatty and nGame % 2000 == 0:
        print("Games Processed:", nGame)
    #path = game.getPathFromRoot()
    #if (path != []):
    #    print(path)
    #    ((ox, oy), (dx, dy)) = path[0]
    #    if dx == 0 and dy >= 5:
    #        debugShow = True
    gkey = game.getKey()
    #node = (game, parent, parent_move)
    gamesSeenAtDepth.put(gkey, depth)
    moves = game.updateAttackFootps(True)
    #if debugShow:
    #    game.show()
    #    print("depth=", depth, "Parent move:", parent_move)
    #    print(game.getBoard())
    ve = verify(game, moves)
    if ve != "ok":
        #if debugShow:
        #    print("Verification was not ok????", "depth=", depth, "player:", game.getMovingPlayer())
        #    exit()
        return "Done here"
    if (depth >= max_depth):
        return "Deep enough"
    #if debugShow:
    #    print("Moves found:", moves)
    #exit()
    thisPlayer = game.getMovingPlayer()
    nextGameNum = nGame + 1
    nextDepth = depth + 1
    lmoves = len(moves)
    nbadmoves = 0
    for m in moves:
        #nm = nm + 1
        #print("Depth", depth, "Move #", nm, "Player", game.getTurn(), "Creating child game with move:", m)
        # Simulate move to check if resulting board has already been seen
        (childBoard, childKey) = game.simulateMove(m)
        dLastSeen = gamesSeenAtDepth.get(childKey)
        if (dLastSeen < depth):
            #if (debugShow):
            #    print("childBoard (from simulated move)")
            #    print(childBoard)
            #    print("childKey", childKey)
            #    print("Revisiting that one, really?")
            #    exit()
            nGamesRevisited = nGamesRevisited + 1
            if chatty and nGamesRevisited % 10000 == 0:
                print("Games Revisited:", nGamesRevisited)
            continue
        # First time seeing this game, or we might have seen this game before,
        # but if so, it was at a deeper depth. So we need to explore it further
        # down from up here.
        # Generate new child game and do apply move to explore further
        childGame = ChessGame()
        childGame.setNum(nextGameNum, nextDepth)
        childGame.initFromParentGame(game, m, childBoard, childKey)
        childGame.updateAttackFootps(False)
        if childGame.getNumChecks(thisPlayer) > 0:
            #print("Move", m, "is NOT valid, skipping")
            nbadmoves = nbadmoves + 1   # Bad move, discard
            continue
        # Valid move
        #if debugShow:
        #    print("Move", m, "is valid, recursing")
        childGame.flipTurn()
        evaluate_recursively(game, m, childGame, nextDepth)
    if (nbadmoves == lmoves):
        # We ultimately had no valid moves in this game, looks like Game over
        result = verify(game, [])
        #exit()
    return "Subtree processed"

def verify(game, moves):
    global nGame
    global wins_per_depth
    global draws_per_depth
    global showEndGames
    depth = game.getDepth()
    if (game.getNpcs(0) + game.getNpcs(1) == 2):
        draws_per_depth[depth] = draws_per_depth[depth] + 1
        if showEndGames:
            game.show()
        print(nGame, "DRAW (only both Kings remain) found at game #", game.getNum(), "depth", depth)
        return "GAME OVER: DRAW"
    if (moves == []):
        nchks = game.getNumChecks(game.getMovingPlayer())
        if (nchks > 0):
            if (nchks > 2):
                error_msg = "ERROR: invalid scenario: more than two checks simultaneously on "+game.getTurn()
                print(error_msg)
                exit()
                #return error_msg
            # No moves and the player to move is under Check -> Game over: LOST the game
            winner = game.getNextTurn()
            wins_per_depth[depth] = wins_per_depth[depth] + 1
            #posWhiteQueen = game.getBoard().find("B",0)
            #if (posWhiteQueen==56):
            #    game.show()
            #    print(nGame, "WIN for", winner, "found at game #", game.getNum(), "depth", depth)
            #    exit()
            print(nGame, "WIN for", winner, "found at game #", game.getNum(), "depth", depth)
            return "GAME OVER: Player", winner, "WINS!"
        else:
            # No moves and not under check -> Game over: DRAW
            #game.setDraw()
            #print("DRAW-------------------------!")
            draws_per_depth[depth] = draws_per_depth[depth] + 1
            if showEndGames:
                game.show()
            print(nGame, "DRAW found at game #", game.getNum(), "depth", depth)
            return "GAME OVER: DRAW"
    return "ok"

def process_options(argv):
    global input_file
    global recurse
    global show_attack_footprints
    global chatty
    global max_depth, wins_per_depth, draws_per_depth
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
                max_depth=int(n)
                wins_per_depth = [0]*(max_depth+1)
                draws_per_depth = [0]*(max_depth+1)
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
        print("ERROR: {0} is not an option, use -h for usage details".format(opt))
        exit(-1)

def mateinx_solver(argv):
    global nGame
    global chatty
    starting_banner()
    process_options(argv)
    start = load_game_from_json()
    game = ChessGame()
    game.initFromJson(start)
    vResults = game.getStatus()
    if (vResults != "OK"):
        print(vResults)
        exit()
    # Aditional validations before starting recursive calls
    origTurn = game.getTurn()
    game.setTurn("w")
    game.updateAttackFootps(False)
    vResults = game.getStatus()
    if (vResults != "OK"):
        game.show()
        print(vResults)
        exit()
    game.setTurn("b")
    game.updateAttackFootps(False)
    vResults = game.getStatus()
    if (vResults != "OK"):
        game.show()
        print(vResults)
        exit()
    if game.getNumChecks(0) > 0 and game.getNumChecks(1) > 0:
        game.show()
        print("ERROR: invalid scenario: both players are under check simultaneously")
        exit()
    game.setTurn(origTurn) # Reset original player moving next
    if (game.getNumChecks(0) > 0 and origTurn=="b") or (game.getNumChecks(1) > 0 and origTurn=="w"):
        game.show()
        print("ERROR: invalid scenario. Player "+origTurn+" will move next -> player "+game.getNextTurn()+" can't be in check")
        exit()
    # At this point, the Game setup was found to be valid
    ngame = 0
    if chatty:
        print("Initial Game configuration is valid\n")
        game.show()
        print(BAR)
    if (recurse):
        evaluate_recursively(None, (), game, 0)
    end_time = time.time()
    print("\nTotal recursive calls:", nRecCalls)
    print("Total games processed:", nGame)
    print("Total games revisited:", nGamesRevisited)
    print("Win-in-X  games found per depth:", wins_per_depth)
    print("Draw-in-X games found per depth:", draws_per_depth)

if __name__ == '__main__':
    mateinx_solver(sys.argv[1:])
