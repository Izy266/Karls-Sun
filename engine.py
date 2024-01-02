from collections import defaultdict
import os, time, mmap, chess, chess.syzygy, chess.polyglot
from pesto import *
from board import *
from tt import *

INFINITY = 15000
MATESCORE = 14500
CHECKMATE = 14000

history_table = defaultdict(lambda: {"killer": 0, "freq": 0})
counter_move_table = defaultdict(list)
killer_table = defaultdict(list)
guess = (0,None)
pvals = [88, 309, 331, 495, 981, 10000, 0]
fmargins = [200, 300, 500, 1000]
current_dir = os.path.dirname(os.path.abspath(__file__))
syzygy_path = os.path.join(current_dir, "syzygy 3-4")
egtb = chess.syzygy.open_tablebase(syzygy_path) # endgame tablebase <= 4 pieces

def hash(gs):
    h = 0
    for i in range(64):
        piece = gs.board[i]
        if piece != 12:
            h ^= gs.zobrist_table[i][piece] 

    if gs.cur_player:
        h ^= gs.zobrist_table[-1]  

    rtc = [gs.wrtc_king_side, gs.wrtc_queen_side, gs.brtc_king_side, gs.brtc_queen_side]
    for i in range(len(rtc)):
        if rtc[i]:
            h ^= gs.zobrist_table[-2 - i]

    enpas = gs.get_enpas()
    if enpas:
        h ^= gs.zobrist_table[-6 - (enpas & 7)]

    return h

def material_left(gs, side = -1):
    count = 0
    locs = [gs.wlocs, gs.blocs]
    locs = [locs[side]] if side > -1 else locs
    for loc in locs:
        for piece in loc:
            count += len(loc[piece])
    return count

def material_balance(gs):
    locs = [gs.wlocs, gs.blocs]
    bal = 0
    for piece in locs[gs.cur_player]:
        bal += pvals[piece >> 1]*(len(locs[gs.cur_player][piece]) - len(locs[gs.cur_player^1][((piece >> 1) << 1) + gs.cur_player^1]))
    return bal

def mvv_lva(gs, moves):
    victim_to_attackers = defaultdict(list)

    for attacker, victim in moves:
        victim_to_attackers[victim].append(attacker)

    sorted_moves = [
        (attacker, victim)
        for victim in sorted(
            victim_to_attackers.keys(), key=lambda v: gs.board[v], reverse=True
        )
        for attacker in victim_to_attackers[victim]
    ]
    return sorted_moves

def order_moves(gs, moves, depth = None):
    promo_moves, capture_moves, check_moves, quiet_moves = [], [], [], []
    history_rel = defaultdict(lambda: 0)
    killer_moves = killer_table[depth]
    promo_ranks = (5, 6) if gs.cur_player else (1, 2)

    for start, end in moves:
        if start//8 in promo_ranks and gs.board[start] >> 1 == 0:
            promo_moves.append((start, end))
        elif gs.board[end] != 12:
            capture_moves.append((start, end))
        # elif move_is_check(gs, (start, end)):
        #     check_moves.append((start, end))
        else:
            quiet_moves.append((start, end))

    capture_moves = mvv_lva(gs, capture_moves)

    for move in quiet_moves:
        if move in killer_moves:
            history_rel[move] = 1.1 + killer_moves.index(move)
        else:
            kill_freq = history_table[move, gs.cur_player]
            cm = 0.075 if gs.prev_moves and gs.prev_moves[-1] == counter_move_table[move, gs.cur_player] else 0
            history_rel[move] = (kill_freq["killer"] / max(1, kill_freq["freq"])) + cm
    quiet_moves.sort(key=lambda move: history_rel.get(move, 0), reverse=True)

    noisy_moves_len = len(promo_moves) + len(capture_moves) + len(check_moves)

    return promo_moves + capture_moves + check_moves + quiet_moves, noisy_moves_len

def get_valid_moves(gs):
    valid_moves = []
    locs = gs.wlocs if gs.cur_player == 0 else gs.blocs

    for starts in locs.values():
        for start in starts:
            valid_moves += gs.generate_moves(start)

    return valid_moves

def get_noisy_moves(gs):
    if gs.check:
        return get_valid_moves(gs)
    
    promo_moves, capture_moves = [], []
    locs = gs.wlocs if gs.cur_player == 0 else gs.blocs
    promo_rank = 6 if gs.cur_player else 2

    for starts in locs.values():
        for start in starts:
            for move in gs.generate_moves(start):
                start, end = move
                if start//8 == promo_rank and gs.board[start] >> 1 == 0:
                    promo_moves.append(move) 
                elif gs.board[end] != 12:
                    capture_moves.append(move)
    
    capture_moves = mvv_lva(gs, capture_moves)
    return capture_moves + promo_moves

def make_null_move(gs):
    gs.cur_player ^= 1
    fen_parts = gs.all_board_positions[-1].split(" ")
    fen_parts[1] = 'b' if fen_parts[1] == 'w' else 'w'
    fen = " ".join(fen_parts)
    gs.all_board_positions[-1] = fen

def move_is_check(gs, move):
    check = False
    start, end = move
    start_piece, end_piece = gs.board[start], gs.board[end]
    side = start_piece & 1
    kloc = gs.wlocs[10][0] if side else gs.blocs[11][0]
    gs.board[start] = 12
    gs.board[end] = start_piece
    if not gs.king_safe(kloc, side ^ 1):
        check = True
    gs.board[start] = start_piece
    gs.board[end] = end_piece
    return check

def get_smallest_attacker(gs, loc, side):
    queen = None
    king = None
    king_safe = True

    # check if pawn is attacking the square
    offs = [7, 9] if side == 0 else [-7, -9]
    for off in offs:
        new_loc = loc + off
        if gs.on_board(off, loc, new_loc) and gs.board[new_loc] == side:
            return new_loc
            
    # Check if knight is attacking the square
    for off in [10, -10, 6, -6, 17, -17, 15, -15]:
        new_loc = loc + off
        if gs.on_board(off, loc, new_loc):
            piece = gs.board[new_loc]
            if piece == 2 + side: # Knight
                return new_loc
            if piece == 2 + side ^ 1: # If knight defending
                king_safe = False     # king can't capture
    
    # Check if square is attacked diagonally
    for off in [9, -9, 7, -7]:
        for new_loc in range(loc + off, -1 if off < 0 else 64, off):
            if not gs.on_board(off, loc, new_loc):
                break
            piece = gs.board[new_loc]
            if piece == 4 + side:
                return new_loc
            if piece == 8 + side:
                queen = new_loc
            elif piece == 10 + side and new_loc == loc + off:
                king = new_loc
            elif piece != 12:
                if piece in [4 + side ^ 1, 8 + side ^ 1] or (piece == 10 + side ^ 1 and new_loc == loc + off):
                    king_safe = False
                break

    # Check if square is attacked horizontally or vertically
    for off in [8, -8, 1, -1]:
        for new_loc in range(loc + off, -1 if off < 0 else 64, off):
            if not gs.on_board(off, loc, new_loc):
                break
            piece = gs.board[new_loc]
            if piece == 6 + side:
                return new_loc
            if piece == 8 + side:
                queen = new_loc
            elif piece == 10 + side and new_loc == loc + off:
                king = new_loc
            elif piece != 12:
                if piece in [6 + side ^ 1, 8 + side ^ 1] or (piece == 10 + side ^ 1 and new_loc == loc + off):
                    king_safe = False
                break

    if queen:
        return queen

    # Check if pawn is defending the square
    offs = [7, 9] if side == 1 else [-7, -9]
    for off in offs:
        new_loc = loc + off
        if gs.on_board(off, loc, new_loc) and gs.board[new_loc] == side ^ 1:
            king_safe = False

    return king if king_safe else None

def see(gs, loc, side):
    value = 0
    attacker = get_smallest_attacker(gs, loc, side)
    attacker_piece = gs.board[attacker] if attacker else None
    victim_piece = gs.board[loc]
    if attacker:
        gs.board[attacker] = 12
        gs.board[loc] = attacker_piece
        value = max(0, pvals[victim_piece >> 1] - see(gs, loc, side ^ 1))
        gs.board[loc] = victim_piece
        gs.board[attacker] = attacker_piece
    return value

def see_capture(gs, start, end, side):
    value = 0
    start_piece = gs.board[start]
    end_piece = gs.board[end]
    gs.board[start] = 12
    gs.board[end] = start_piece
    value = pvals[end_piece >> 1] - see(gs, end, side ^ 1)
    gs.board[start] = start_piece
    gs.board[end] = end_piece
    return value

def quiesce(gs, alpha, beta, trans_table, depth = 0):
    if round(time.time()*1000) - get_time(trans_table, "start") > get_time(trans_table, "max") * 0.99:
        trans_table[-1] = 1

    if trans_table[-1] == 0:
        node_count(trans_table, "add")
        if gs.checkmate:
            return -MATESCORE + depth
        elif gs.stalemate or gs.draw:
            return 0
        
        alpha_og = alpha
        zobrist = hash(gs)
        tt_entry = get_tt(trans_table, zobrist)

        if tt_entry and tt_entry[-1] == (1, 1):
            tt_score, tt_flag, tt_depth = tt_entry[0], tt_entry[1], tt_entry[2]
            if tt_score < -CHECKMATE:
                tt_score -= tt_depth
            elif tt_score > CHECKMATE:
                tt_score += tt_depth
            if tt_flag == 0:
                return tt_score
            elif tt_flag == 1:
                alpha = max(alpha, tt_score)
            elif tt_flag == 2:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score
                             
        stand_pat = pesto(gs)

        if stand_pat >= beta and not gs.check:
            return beta
        
        # delta pruning
        big_delta = 1025
        if stand_pat < alpha - big_delta:
            return alpha

        if stand_pat > alpha:
            alpha = stand_pat    

        for move in get_noisy_moves(gs):
            start = move[0]
            end = move[1] if not gs.promo_move(start) else gs.parse_promo(start, move[1])[0]
            piece_end = gs.board[end]

            if (
                piece_end != 12 and 
                (stand_pat + pvals[piece_end >> 1] + fmargins[0] <= alpha or
                see_capture(gs, start, end, gs.cur_player) < 0)
            ):
                continue

            gs.move(move)
            score = -quiesce(gs, -beta, -alpha, trans_table, depth - 1)
            gs.undo()
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        if trans_table[-1] == 0:
            tt_flag = (
                2 # upperbound
                if alpha <= alpha_og
                else 1 # lowerbound
                if alpha >= beta
                else 0 # exact
            )

            tt_score = alpha
            if tt_score < -CHECKMATE:
                tt_score = -MATESCORE + depth
            elif tt_score > CHECKMATE:
                tt_score = MATESCORE - depth
            store_tt(trans_table, zobrist, tt_score, tt_flag, 0, (1, 1))

    return alpha

def negamax_root(gs, depth, alpha, beta, trans_table, moves = None, allow_null = True):    
    best_score = -INFINITY
    best_move = (0, 0)

    if trans_table[-1] == 0:
        node_count(trans_table, "add")
        alpha_og = alpha
        zobrist = hash(gs)
        tt_entry = get_tt(trans_table, zobrist)

        if gs.all_board_positions.count(gs.all_board_positions[-1]) < 2 and tt_entry:
            tt_score, tt_flag, tt_depth, tt_move = tt_entry
            if tt_depth >= depth and tt_move != (1, 1):
                if tt_score < -CHECKMATE:
                    tt_score -= tt_depth
                elif tt_score > CHECKMATE:
                    tt_score += tt_depth
                if tt_flag == 0:
                    set_best(trans_table, tt_score, tt_move, tt_depth)
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    set_best(trans_table, tt_score, tt_move, tt_depth)
                    return tt_score
                
        valid_moves = get_valid_moves(gs) if not moves else moves
        noisy_moves_len = 0
        random.shuffle(valid_moves)
        valid_moves, noisy_moves_len = order_moves(gs, valid_moves, depth)  

        for m, move in enumerate(valid_moves):
            if trans_table[-1] != 0:
                break
            
            move = valid_moves[m]
            start_square = move[0]
            promo_move = gs.promo_move(start_square)
            end_square = move[1] if not promo_move else gs.parse_promo(start_square, move[1])[0]
            end_piece = gs.board[end_square]

            gs.move(move)
            quiet_move = m >= noisy_moves_len
            
            # extended futility pruning
            if (
                depth < 3
                and quiet_move
                and not gs.check
                and abs(alpha) < CHECKMATE
                and abs(beta) < CHECKMATE
                and material_left(gs, gs.cur_player) > 3
            ):
                if -material_balance(gs) + fmargins[depth] <= alpha:
                    gs.undo()
                    continue
            
            # late move reduction and razoring
            if (
                depth >= 3
                and not gs.check
                and (m >= noisy_moves_len + 3 or (quiet_move and depth == 3 and -material_balance(gs) + fmargins[3] <= alpha))
            ):
                r = max(2, depth//3) if m > noisy_moves_len + 10 else 1
                score = -negamax(gs, depth - r - 1, -beta, -alpha, trans_table)
                if score > alpha:
                    score = -negamax(gs, depth - 1, -beta, -alpha, trans_table)
            else:
                score = -negamax(gs, depth - 1, -beta, -alpha, trans_table)

            gs.undo()

            if trans_table[-1] == 0:
                if end_piece == 12:
                    history_table[move, gs.cur_player]["freq"] += 1

                if score >= best_score:
                    best_score = score
                    best_move = move if best_move == (0, 0) else best_move
                    if score > alpha:
                        alpha = score
                        best_move = move
                        set_best(trans_table, best_score, best_move, depth)

                if alpha >= beta:
                    if end_piece == 12:
                        if move not in killer_table[depth]:
                            killer_table[depth].append(move)
                        history_table[move, gs.cur_player]["killer"] += 2**depth
                        counter_move_table[move, gs.cur_player] = gs.prev_moves[-1] if gs.prev_moves else None
                        killer_table[depth] = killer_table[depth][-3:]             
                    break

        if trans_table[-1] == 0:
            tt_flag = (
                2 # upperbound
                if best_score <= alpha_og
                else 1 # lowerbound
                if best_score >= beta
                else 0 # exact
            )

            if (
                not tt_entry 
                or depth >= tt_entry[2]
            ):
                tt_score = best_score
                if tt_score < -CHECKMATE:
                    tt_score = -MATESCORE + depth
                elif tt_score > CHECKMATE:
                    tt_score = MATESCORE - depth
                store_tt(trans_table, zobrist, tt_score, tt_flag, depth, best_move)

    return best_score

def negamax(gs, depth, alpha, beta, trans_table, allow_null=True):
    best_score = -INFINITY
    best_move = (0, 0)

    if round(time.time()*1000) - get_time(trans_table, "start") > get_time(trans_table, "max") * 0.99:
        trans_table[-1] = 1

    if trans_table[-1] == 0:
        node_count(trans_table, "add")
        if gs.checkmate:
            return -MATESCORE - depth
        elif gs.stalemate or gs.draw:
            return 0
        
        alpha_og = alpha
        zobrist = hash(gs)
        tt_entry = get_tt(trans_table, zobrist)

        if gs.all_board_positions.count(gs.all_board_positions[-1]) < 2 and tt_entry:
            tt_score, tt_flag, tt_depth, tt_move = tt_entry
            if tt_depth >= depth and tt_move != (1, 1):
                if tt_score < -CHECKMATE:
                    tt_score -= tt_depth
                elif tt_score > CHECKMATE:
                    tt_score += tt_depth
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score
        
        if depth <= 0:
            return quiesce(gs, alpha, beta, trans_table)
        
        fmargin = fmargins[depth] if depth < 4 else 300*depth

        # reverse futility pruning
        if (
            0 < depth <= 6
            and not gs.check
            and abs(alpha) < CHECKMATE
            and abs(beta) < CHECKMATE
        ):
            fut_eval = pesto(gs) - fmargin
            if fut_eval >= beta:
                return fut_eval

        threat = False
        # null move reduction
        if (
            not gs.check 
            and allow_null
        ):
            r = 4 if depth > 6 else 3
            make_null_move(gs)
            score = -negamax(gs, depth - r - 1, -beta, -beta + 1, trans_table, False)
            make_null_move(gs)

            if score >= beta:
                depth -= 4
                if depth <= 0:
                    return quiesce(gs, alpha, beta, trans_table)

            # mate threat extension logic
            elif score < -CHECKMATE:
                threat = True

        valid_moves = order_moves(gs, get_valid_moves(gs), depth)   
        noisy_moves_len = valid_moves[1]
        valid_moves = valid_moves[0]

        for m, move in enumerate(valid_moves):
            if trans_table[-1] != 0:
                break
            
            move = valid_moves[m]
            start_square = move[0]
            promo_move = gs.promo_move(start_square)
            end_square = move[1] if not promo_move else gs.parse_promo(start_square, move[1])[0]
            end_piece = gs.board[end_square]

            ext = (
                threat or                                                    # mate threat extension
                len(valid_moves) == 1 or                                     # one reply extension
                gs.check or                                                  # check extension
                promo_move                                                   # promotion extension
                # add recapture extension
            )

            gs.move(move)
            
            ext = False if gs.check else ext
            quiet_move = m >= noisy_moves_len

            # extended futility pruning
            if (
                depth < 3
                and quiet_move
                and not ext
                and not gs.check
                and abs(alpha) < CHECKMATE
                and abs(beta) < CHECKMATE
                and material_left(gs, gs.cur_player) > 3
            ):
                if -material_balance(gs) + fmargin <= alpha:
                    gs.undo()
                    continue

            # late move reduction and razoring
            if (
                depth >= 3
                and not ext
                and not gs.check
                and (m >= noisy_moves_len + 3 or (quiet_move and depth == 3 and -material_balance(gs) + fmargin <= alpha))
            ):
                r = max(2, depth//3) if m > noisy_moves_len + 10 else 1
                score = -negamax(gs, depth - r - 1, -beta, -alpha, trans_table)
                if score > alpha:
                    score = -negamax(gs, depth - 1, -beta, -alpha, trans_table)
            else:
                score = -negamax(gs, depth - 1 + ext, -beta, -alpha, trans_table)

            gs.undo()

            if trans_table[-1] == 0:
                if end_piece == 12:
                    history_table[move, gs.cur_player]["freq"] += 1

                if score >= best_score:
                    best_score = score
                    if score > alpha:
                        alpha = score
                        best_move = move
                
                if alpha >= beta:
                    if end_piece == 12:
                        if move not in killer_table[depth]:
                            killer_table[depth].append(move)
                        history_table[move, gs.cur_player]["killer"] += 2**depth
                        counter_move_table[move, gs.cur_player] = gs.prev_moves[-1] if gs.prev_moves else None
                        killer_table[depth] = killer_table[depth][-3:]
                    break

        if trans_table[-1] == 0: 
            tt_flag = (
                2 # upperbound
                if best_score <= alpha_og
                else 1 # lowerbound
                if best_score >= beta
                else 0 # exact
            )

            if (
                not tt_entry 
                or depth >= tt_entry[2]
            ):                  
                if tt_entry and best_move == (0, 0):
                    best_move = tt_entry[-1]

                tt_score = best_score
                if tt_score < -CHECKMATE:
                    tt_score = -MATESCORE + depth
                elif tt_score > CHECKMATE:
                    tt_score = MATESCORE - depth
                store_tt(trans_table, zobrist, tt_score, tt_flag, depth, best_move)

    return best_score

def MTDF(gs, guess, depth, trans_table): 
    lower = -INFINITY
    upper = INFINITY
    score = guess
    window = 55

    while lower < upper and trans_table[-1] == 0:
        beta = score + window if score == lower else score
        score = negamax_root(gs, depth, beta - window, beta, trans_table)
        if score < beta:
            upper = score
        else:
            lower = score
    return score

def get_move(args):
    global guess
    global nodes
    gs, max_depth = args
    choices = [-1, 0, -1, -1, -1, -1, 0, -1, -1, 0, -1, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, 0, -1, -1, 0, -1, 0, 0, 0, 0, -1, 0, 0, -1, 0, -1, 0, 0, -1, -1, -1, 0, -1, 0]
    choices2 = [0, -1, -1, -1, -1, 0, -1, -1, 0, -1, 0, -1, -1, 0, -1, 0, -1, 0, -1, -1, 0, 0, 0, -1, -1, -1, 0, -1, 0, 0, -1, 0, 0, -1, -1, 0, 0, 0, 0, 0, 0, -1, -1, 0, 0, -1, 0, -1, -1, 0]
    tt_path = os.path.join(current_dir, "t.dat")
    with open(tt_path, "r+b") as f:
        fd = f.fileno()
        trans_table = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)

    nodes = 0
    cur_depth = 1
    fen = gs.all_board_positions[-1]
    book_path = os.path.join(current_dir, "komodo.bin")

    with chess.polyglot.open_reader(book_path) as reader:
        board = chess.Board(fen)
        moves = []
        for entry in reader.find_all(board):
            best = str(entry.move)
            parsed = (gs.parse_loc(best[:2]), gs.parse_loc(best[2:]))
            moves.append(parsed)
        if moves:
            set_best(trans_table, 0, moves[0], 1)
            trans_table[-1] = 1
            return 1

    if material_left(gs) <= 4:
        no_cap = 1 in [material_left(gs, 0), material_left(gs, 1)]
        wdls, dtzs = [], []
        valid_moves = get_valid_moves(gs)
        for move in valid_moves:
            gs.move(move)
            fen = gs.all_board_positions[-1]
            board = chess.Board(fen)
            wdl = -egtb.probe_wdl(board)
            wdl = 0 if gs.all_board_positions.count(gs.all_board_positions[-1]) > 1 else wdl
            wdls.append(wdl)
            if no_cap:
                dtz = -egtb.probe_dtz(board)
                dtzs.append(dtz)
            gs.undo()

        max_wdl = max(wdls)
        score = 15000 if max_wdl > 0 else -15000 if max_wdl < 0 else 0
        valid_moves = [valid_moves[i] for i in range(len(valid_moves)) if wdls[i] == max_wdl]
        if no_cap:
            dtzs = [dtzs[i] for i in range(len(dtzs)) if wdls[i] == max_wdl] 
            set_best(trans_table, score, valid_moves[dtzs.index(min(dtzs))], 1)
        else:
            negamax_root(gs, min(max_depth, 4), -INFINITY, INFINITY, trans_table, valid_moves)
        trans_table[-1] = 1
        return 1
        
    guess = (guess[0] if guess[1] == gs.cur_player else -guess[0], gs.cur_player)

    # iterative deepening
    while cur_depth <= max_depth and trans_table[-1] == 0:
        guess = (MTDF(gs, guess[0], cur_depth, trans_table), gs.cur_player)
        if abs(guess[0]) > CHECKMATE:
            break
        cur_depth += 1
        depth_reach(trans_table, "set", max(cur_depth, depth_reach(trans_table, "get")))

    trans_table[-1] = 1
    return 1
