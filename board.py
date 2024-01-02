import random

class GameState:
    def __init__(self):
        self.board = [
            7, 3, 5, 9, 11, 5, 3, 7, 
            1, 1, 1, 1, 1, 1, 1, 1, 
            12, 12, 12, 12, 12, 12, 12, 12, 
            12, 12, 12, 12, 12, 12, 12, 12, 
            12, 12, 12, 12, 12, 12, 12, 12, 
            12, 12, 12, 12, 12, 12, 12, 12, 
            0, 0, 0, 0, 0, 0, 0, 0, 
            6, 2, 4, 8, 10, 4, 2, 6
        ]


        self.wlocs = {
            0: [i for i in range(48, 56)],
            2: [57, 62],
            4: [58, 61],
            6: [56, 63],
            8: [59],
            10: [60],
        }

        self.blocs = {
            1: [i for i in range(8, 16)],
            3: [1, 6],
            5: [2, 5],
            7: [0, 7],
            9: [3],
            11: [4],
        }

        # Move offsets for each piece indexed by piece value
        self.offsets_map = [
            [8, 7, 9],
            [17, -17, 15, -15, 10, -10, 6, -6],
            [9, -9, 7, -7],
            [8, -8, 1, -1],
            [9, -9, 8, -8, 7, -7, 1, -1],
            [9, -9, 8, -8, 7, -7, 1, -1],
        ]

        self.num_to_piece = [
            "P",
            "p",
            "N",
            "n",
            "B",
            "b",
            "R",
            "r",
            "Q",
            "q",
            "K",
            "k",
            ".",
        ]
        self.piece_to_num = {
            "P": 0,
            "p": 1,
            "N": 2,
            "n": 3,
            "B": 4,
            "b": 5,
            "R": 6,
            "r": 7,
            "Q": 8,
            "q": 9,
            "K": 10,
            "k": 11,
        }

        self.white_captured, self.black_captured = [], []
        self.check, self.checkmate = False, False
        self.draw, self.stalemate = False, False
        self.wrtc_king_side, self.wrtc_queen_side = True, True
        self.brtc_king_side, self.brtc_queen_side = True, True
        self.white_atkd, self.black_atkd = [], []
        self.cur_player = 0
        self.prev_moves = []
        self.promo = False

        self.all_board_positions = [self.board_to_fen()]
        self.zobrist_table = self.init_zobrist()

    def init_zobrist(self):
        table = [[random.getrandbits(64) for _ in range(12)] for _ in range(64)]

        # bitstrings for castling rights and enpasant files
        for i in range(13):
            table.append(random.getrandbits(64))

        return table

    def print_board(self):
        for i in range(0, 64, 8):
            row = self.board[i : i + 8]
            row_pieces = [self.num_to_piece[piece] for piece in row]
            print("  ".join(row_pieces))

    def parse_loc(self, loc):
        return ((8 - int(loc[1])) << 3) + ord(loc[0]) - 97

    def parse_index(self, index):
        return f"{chr(97 + (index & 7))}{8 - (index >> 3)}"

    def move_piece(self, start, end):
        piece_start, piece_end = self.board[start], self.board[end]
        locs = self.blocs if piece_start & 1 else self.wlocs

        locs[piece_start][locs[piece_start].index(start)] = end
        self.board[start] = 12
        self.board[end] = piece_start

        if piece_end != 12:
            locs = self.blocs if piece_end & 1 else self.wlocs
            locs[piece_end].remove(end)

    def set_piece(self, loc, piece):
        piece_at_loc = self.board[loc]
        self.board[loc] = piece

        if piece != 12:
            locs = self.blocs if piece & 1 else self.wlocs
            locs[piece].append(loc)

        if piece_at_loc != 12:
            locs = self.blocs if piece_at_loc & 1 else self.wlocs
            locs[piece_at_loc].remove(loc)

    def update_captures(self):
        self.white_captured, self.black_captured = [], []
        for piece in self.wlocs:
            diff = len(self.wlocs[piece]) - len(self.blocs[piece + 1])
            for _ in range(diff):
                self.white_captured.append(piece + 1)
            for _ in range(-diff):
                self.black_captured.append(piece)

    def undo(self):
        self.check, self.checkmate = False, False
        self.draw, self.stalemate = False, False

        if len(self.all_board_positions) > 1:
            self.all_board_positions.pop()
        if len(self.prev_moves) > 0:
            self.prev_moves.pop()

        self.build_fen(self.all_board_positions[-1], False)

    def get_enpas(self):
        if self.prev_moves:
            start, end = self.prev_moves[-1]
            if (
                (start >> 3, end >> 3) in [(1, 3), (6, 4)]
                and abs(start - end) == 16
                and self.board[end] >> 1 == 0
            ):
                return start + 8 if start >> 3 == 1 else start - 8

    def board_to_fen(self):
        side = "wb"[self.cur_player]
        rtc = (
            "".join(
                [
                    "K" if self.wrtc_king_side else "",
                    "Q" if self.wrtc_queen_side else "",
                    "k" if self.brtc_king_side else "",
                    "q" if self.brtc_queen_side else "",
                ]
            )
            or "-"
        )
        enpas = self.get_enpas()
        enpas = self.parse_index(enpas) if enpas else "-"

        board_fen = ""
        empty = 0
        for i in range(64):
            if i % 8 == 0 and i != 0:
                if empty != 0:
                    board_fen += str(empty)
                    empty = 0
                board_fen += "/"

            if self.board[i] == 12:
                empty += 1
            else:
                if empty != 0:
                    board_fen += str(empty)
                    empty = 0
                board_fen += self.num_to_piece[self.board[i]]

        if empty != 0:
            board_fen += str(empty)

        return f"{board_fen} {side} {rtc} {enpas}"

    def build_fen(self, fen, new=True):
        board_fen, side, rtc, enpas = fen.split()[:4]

        for piece in self.wlocs:
            self.wlocs[piece] = []
        for piece in self.blocs:
            self.blocs[piece] = []

        self.board = [12] * 64
        fen_ind = 0
        for char in board_fen:
            if char.isdigit():
                fen_ind += int(char)
            elif char.isalpha():
                piece = self.piece_to_num[char]
                self.board[fen_ind] = piece
                if piece & 1:
                    self.blocs[piece].append(fen_ind)
                else:
                    self.wlocs[piece].append(fen_ind)
                fen_ind += 1

        self.update_captures()
        self.promo = False
        self.cur_player = 0 if side == "w" else 1
        self.wrtc_king_side = "K" in rtc
        self.wrtc_queen_side = "Q" in rtc
        self.brtc_king_side = "k" in rtc
        self.brtc_queen_side = "q" in rtc

        self.check = not self.king_safe(
            self.wlocs[10 + self.cur_player][0]
            if self.cur_player == 0
            else self.blocs[10 + self.cur_player][0],
            self.cur_player,
        )

        if enpas != "-":
            enpas_loc = self.parse_loc(enpas)
            start = enpas_loc + 8 if enpas[-1] == "3" else enpas_loc - 8
            end = enpas_loc - 8 if enpas[-1] == "3" else enpas_loc + 8
            if new:
                self.prev_moves = [(start, end)]

        if new:
            self.all_board_positions = [fen]

    def is_black_square(self, index):
        return ((index >> 3) + (index & 7)) & 1 == 1

    def promo_move(self, start):
        return (start >> 3 == 6 and self.board[start] == 1) or (
            start >> 3 == 1 and self.board[start] == 0
        )

    def parse_promo(self, start, end, move_played=False):
        side = self.cur_player if not move_played else self.cur_player ^ 1
        offs = [7, 8, 9] if side else [-7, -8, -9]
        ends = [start + o for o in offs if 0 <= start + o < 64]
        for i in range(1, 5):
            if end - (i << 2) in ends:
                return end - (i << 2), (i << 1)

    def check_mate(self):
        locs = self.blocs if self.cur_player else self.wlocs
        for piece in [2, 8, 6, 4, 0, 10]:
            for loc in locs[piece + self.cur_player]:
                if self.generate_moves(loc, test=True):
                    return False

        if self.check:
            self.checkmate = True
        else:
            self.stalemate = True

    def insufficient(self):
        # Check for pawns, rooks, and queens
        major_pieces = [0, 1, 6, 7, 8, 9]
        if any(len(self.wlocs.get(piece, [])) > 0 for piece in major_pieces) or any(
            len(self.blocs.get(piece, [])) > 0 for piece in major_pieces
        ):
            return False

        # Check for more than one minor piece
        minor_pieces = [2, 3, 4, 5]
        white_minor_pieces = sum(
            len(self.wlocs.get(piece, [])) for piece in minor_pieces
        )
        black_minor_pieces = sum(
            len(self.blocs.get(piece, [])) for piece in minor_pieces
        )
        if white_minor_pieces > 1 or black_minor_pieces > 1:
            return False

        # Check for bishops of opposite colors
        if len(self.wlocs[4]) and len(self.blocs[5]):
            white_bishop_square = self.wlocs[4][0]
            black_bishop_square = self.blocs[5][0]
            if self.is_black_square(white_bishop_square) != self.is_black_square(
                black_bishop_square
            ):
                return False

        return True

    def check_horizontal_attacks(self, loc, side):
        attacking_pieces = [6 + side ^ 1, 8 + side ^ 1]  # Rook and Queen

        # Check right and left
        for off in [1, -1]:
            for new_loc in range(
                loc + off,
                ((loc >> 3) << 3) + 8 if off > 0 else ((loc >> 3) << 3) - 1,
                off,
            ):  # Stay within the same rank
                piece = self.board[new_loc]
                if piece in attacking_pieces or (
                    new_loc == loc + off and piece == 10 + side ^ 1
                ):  # or king and one square away
                    return False
                elif piece not in [
                    12,
                    10 + side,
                ]:  # Stop if there's a piece blocking the way
                    break

        return True

    def check_vertical_attacks(self, loc, side):
        attacking_pieces = [6 + side ^ 1, 8 + side ^ 1]  # Rook and Queen

        # Check down and up
        for off in [8, -8]:
            for new_loc in range(
                loc + off, 64 if off > 0 else -1, off
            ):  # Stay within the board
                piece = self.board[new_loc]
                if piece in attacking_pieces or (
                    new_loc == loc + off and piece == 10 + side ^ 1
                ):  # or king and one square away
                    return False
                elif piece not in [
                    12,
                    10 + side,
                ]:  # Stop if there's a piece blocking the way
                    break

        return True

    def check_diagonal_attacks(self, loc, side):
        attacking_pieces = [4 + side ^ 1, 8 + side ^ 1]  # Bishop and Queen

        # Check all four diagonals
        for off in [9, -9, 7, -7]:
            pdir = (off < 0 and side == 0) or (off > 0 and side == 1)
            for new_loc in range(loc + off, -1 if off < 0 else 64, off):
                if abs((new_loc >> 3) - (loc >> 3)) != abs(
                    (new_loc & 7) - (loc & 7)
                ):  # Stop if not on the same diagonal, i.e border is traversed
                    break
                piece = self.board[new_loc]
                if piece in attacking_pieces or (
                    new_loc == loc + off
                    and (piece == 10 + side ^ 1 or pdir and piece == side ^ 1)
                ):  # or (king or (pawn and pawn direction)) and one square away
                    return False
                elif piece not in [
                    12,
                    10 + side,
                ]:  # Stop if there's a piece blocking the way
                    break

        return True

    def check_knight_attacks(self, loc, side):
        attacking_piece = 2 + side ^ 1  # Knight
        for off in [10, -10, 6, -6, 17, -17, 15, -15]:
            new_loc = loc + off
            if (
                0 <= new_loc < 64 and abs((new_loc & 7) - (loc & 7)) <= 2
            ):  # Stay within the board without traversing border
                if self.board[new_loc] == attacking_piece:
                    return False
        return True

    def king_safe(self, loc, side):
        check_functions = [
            self.check_diagonal_attacks,
            self.check_knight_attacks,
            self.check_horizontal_attacks,
            self.check_vertical_attacks,
        ]
        return all(check(loc, side) for check in check_functions)

    def test_king_safety(self, move):
        side = self.cur_player
        kloc = self.wlocs[10][0] if side == 0 else self.blocs[11][0]
        start, end = move[0], move[1]

        if not self.check:
            vertical = start & 7 == kloc & 7
            horizontal = start >> 3 == kloc >> 3
            diag = abs((start >> 3) - (kloc >> 3)) == abs((start & 7) - (kloc & 7))

            if not (vertical or horizontal or diag):
                return True

            piece_start = self.board[start]
            if piece_start >> 1 != 1:
                if (vertical and end & 7 == kloc & 7) or (
                    horizontal and end >> 3 == kloc >> 3
                ):
                    return True

                if (
                    diag
                    and abs((start >> 3) - (end >> 3)) == abs((start & 7) - (end & 7))
                    and abs((end >> 3) - (kloc >> 3)) == abs((end & 7) - (kloc & 7))
                ):
                    return True

            self.board[start] = 12
            king_safe = (
                self.check_vertical_attacks(kloc, side)
                if vertical
                else self.check_horizontal_attacks(kloc, side)
                if horizontal
                else self.check_diagonal_attacks(kloc, side)
            )
            self.board[start] = piece_start
            return king_safe
        else:
            piece_start, piece_end = self.board[start], self.board[end]
            self.board[start], self.board[end] = 12, piece_start
            king_safe = self.king_safe(kloc, side)
            self.board[start], self.board[end] = piece_start, piece_end
            return king_safe

    # A check function to ensure piece hasen't traversed the border
    def on_board(self, offset, start, end):
        if not (0 <= end < 64):
            return False

        # If movement is horizontal ensure piece is on the same row
        if abs(offset) == 1:
            return start >> 3 == end >> 3

        # If movement is diagonal, ensure piece is on the same diagonal
        if abs(offset) in [7, 9]:
            return abs((start >> 3) - (end >> 3)) == abs((start & 7) - (end & 7))

        # If knight movement, ensure knight is within 2 files of starting position
        if abs(offset) in [6, 10, 15, 17]:
            return abs((end & 7) - (start & 7)) <= 2

        return True

    def generate_moves(self, start, test=False):
        piece = self.board[start]
        piece_value = piece >> 1
        piece_color = piece & 1
        end = start
        safe = False
        moves = []

        # Generate all pseudo-legal moves for the piece
        for off in self.offsets_map[piece_value]:
            off = -off if piece == 0 else off
            end = start + off
            safe = safe if piece_value == 1 else False

            # If piece is pawn
            if piece_value == 0:
                if self.on_board(off, start, end):
                    piece_end = self.board[end]
                    if (off in (8, -8) and piece_end != 12) or (
                        off & 7
                        and (piece_end == 12 or piece_end & 1 == piece_color)
                        and end != self.get_enpas()
                    ):
                        continue

                    if self.test_king_safety((start, end)):
                        if test:
                            return True
                        # If pawn promoting
                        if end >> 3 in (0, 7):
                            moves += [(start, end + (i << 2)) for i in range(1, 5)]
                        # If pawn on home rank
                        elif not off & 7 and start >> 3 == (6 if piece == 0 else 1):
                            safe = not self.check
                            moves.append((start, end))
                            if self.board[end + off] == 12 and (
                                safe or self.test_king_safety((start, end + off))
                            ):
                                if test:
                                    return True
                                moves.append((start, end + off))
                        else:
                            moves.append((start, end))

            # If piece is king
            elif piece_value == 5:
                if self.on_board(off, start, end):
                    piece_end = self.board[end]
                    if piece_end != 12 and piece_end & 1 == piece_color:
                        continue
                    if self.king_safe(end, piece_color):
                        if test:
                            return True
                        moves.append((start, end))
                        if not self.check and piece_end == 12 and off in (1, -1):
                            castle = (
                                self.brtc_queen_side
                                if piece_color
                                else self.wrtc_queen_side
                            )
                            if off == 1:
                                castle = (
                                    self.brtc_king_side
                                    if piece_color
                                    else self.wrtc_king_side
                                )
                            if (
                                castle
                                and all(
                                    self.board[start + i * off] == 12
                                    for i in range(2, 3 if off == 1 else 4)
                                )
                                and self.king_safe(start + 2 * off, piece_color)
                            ):
                                moves.append((start, start + 2 * off))

            # If piece is queen, rook, bishop or knight
            else:
                tried = False
                while self.on_board(off, start, end):
                    piece_end = self.board[end]

                    # If we encounter another piece of the same color, stop
                    if piece_end != 12 and piece_end & 1 == piece_color:
                        break

                    tried = True
                    # If move doesn't result in ally king being in check
                    if safe or self.test_king_safety((start, end)):
                        if test:
                            return True
                        safe = not self.check
                        moves.append((start, end))

                    # If end square is not empty or start piece is knight, break.
                    if (
                        piece_end != 12
                        or (not safe and not self.check)
                        or piece_value == 1
                    ):
                        break
                    end += off

                # If knight is pinned, stop
                if piece_value == 1 and tried and not safe and not self.check:
                    break
        return moves

    def move(self, move):
        start = move[0]
        self.promo = True if self.promo_move(start) else False
        end = move[1] if not self.promo else self.parse_promo(start, move[1])[0]

        piece_start = self.board[start]
        piece_end = self.board[end]

        self.check = False
        self.move_piece(start, end)

        self.prev_moves.append(move)

        # if piece is pawn
        if piece_start >> 1 == 0:
            off = 8 if self.cur_player == 0 else -8
            # handle promotion
            if self.promo:
                self.set_piece(
                    end, self.parse_promo(start, move[1])[1] + self.cur_player
                )
            # if enpassant
            elif piece_end == 12 and start & 7 != end & 7:
                self.set_piece(end + off, 12)

        # if piece is king
        elif piece_start >> 1 == 5:
            if self.cur_player == 0:
                self.wrtc_king_side, self.wrtc_queen_side = False, False
            else:
                self.brtc_king_side, self.brtc_queen_side = False, False
            # handle castling
            for path in (1, -1):
                if (start & 7) - (end & 7) == path << 1:
                    if path == 1:
                        self.move_piece(0 if self.cur_player else 56, end + path)
                    else:
                        self.move_piece(7 if self.cur_player else 63, end + path)

        # if piece is rook
        rook_loc = (
            start if piece_start >> 1 == 3 else end if piece_end >> 1 == 3 else None
        )
        if rook_loc is not None:
            rook_castling_map = {
                63: "wrtc_king_side",
                56: "wrtc_queen_side",
                7: "brtc_king_side",
                0: "brtc_queen_side",
            }
            if rook_loc in rook_castling_map:
                setattr(self, rook_castling_map[rook_loc], False)

        if piece_end != 12:
            self.update_captures()

        self.cur_player ^= 1

        locs = self.wlocs if self.cur_player == 0 else self.blocs
        if not self.king_safe(locs[10 + self.cur_player][0], self.cur_player):
            self.check = True

        self.check_mate()
        fen = self.board_to_fen()
        self.all_board_positions.append(fen)
        self.draw = self.all_board_positions.count(fen) > 2 or self.insufficient()
