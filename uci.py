import re
import multiprocessing as mp
from engine import *

def parse_command(command):
    uci_pattern = re.compile(r'^uci$')
    isready_pattern = re.compile(r'^isready$')
    position_pattern = re.compile(r'^position\s+(startpos|fen\s+(.*?))(\s+moves\s+(.*))?$')
    go_pattern = re.compile(r'^go\s+(.*)$')
    move_pattern = re.compile(r'^move\s+(\w\d)\s+(\w\d)(\s*([qrbn]))?$')
    stop_pattern = re.compile(r'^stop$')
    ucinewgame_pattern = re.compile(r'^ucinewgame$')

    if uci_pattern.match(command):
        return 'uci', None
    elif isready_pattern.match(command):
        return 'isready', None
    elif position_match := position_pattern.match(command):
        fen = position_match.group(2) if position_match.group(2) else 'startpos'
        moves = position_match.group(4)
        return 'position', fen, moves
    elif go_match := go_pattern.match(command):
        params = go_match.group(1)
        return 'go', params
    elif move_match := move_pattern.match(command):
        move_from = move_match.group(1)
        move_to = move_match.group(2)
        promotion = move_match.group(3)
        return 'move', move_from, move_to, promotion
    elif stop_pattern.match(command):
        return 'stop', None
    elif ucinewgame_pattern.match(command):
        return 'ucinewgame', None
    else:
        return "N/A"
    
def parse_engine_move(move):
    start = move[0]
    end = move[1] if not game.promo_move(start) else game.parse_promo(start, move[1])[0]
    promo_piece = ''
    if game.promo_move(start):
        offs = [7,8,9] if game.cur_player else [-7,-8,-9]
        ends = [start + o for o in offs]
        pp_map = ['', 'n', 'b', 'r', 'q']
        for i in range(1,5):
            if move[1] - i*4 in ends:
                promo_piece = pp_map[i]
                break
    return f"{game.parse_index(start)}{game.parse_index(end)}{promo_piece}"

def parse_uci_move(move):
    promo_offs = {'na': 0, 'n': 4, 'b': 8, 'r': 12, 'q': 16}
    promo = move[4] if len(move) > 4 else 'na'
    promo = promo_offs[promo]
    return (game.parse_loc(move[:2]), game.parse_loc(move[2:4]) + promo)

def handle_go(params):
    go = params.split()
    start_time = round(time.time()*1000)
    set_time(trans_table, start_time, "start")
    node_count(trans_table, "clear")
    clear_best(trans_table)
    depth_reach(trans_table, "set", 0)
    trans_table[-1] = 0
    if "depth" in go:
        max_time, max_depth = 65000, int(go[go.index("depth") + 1])
    elif "movetime" in go:
        max_time, max_depth = int(go[go.index("movetime") + 1]), 100
    
    set_time(trans_table, max_time, "max")
    args = [(game, max_depth) for _ in range(cores)]
    pool.map(get_move, args)
    score, move, depth = get_best(trans_table) if get_best(trans_table)[-1] < depth_reach(trans_table, "get") else get_best(trans_table, -2)
    print(f"bestmove {parse_engine_move(move)}")
    
def handle_position(fen, moves):
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" if fen == 'startpos' else fen
    game.build_fen(fen)

    if moves:
        moves = [
            parse_uci_move(move) for move in moves.split()
        ]
        for move in moves:
            game.move(move)

def handle_move(move_from, move_to, promo_piece):
    promo_offs = {None: 0, 'n': 4, 'b': 8, 'r': 12, 'q': 16}
    move_to, move_from = game.parse_loc(move_to), game.parse_loc(move_from)
    move_to += promo_offs[promo_piece]
    game.move((move_from, move_to))

def handle_stop():
    trans_table[-1] = 1

def handle_ucinewgame():
    game.build_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -")

if __name__ == '__main__':
    game = GameState()
    cores = mp.cpu_count()//2 - 1
    pool = mp.Pool(processes=cores)
    tt_size = 520000000 # bytes
    tt_path = os.path.join(current_dir, "t.dat")

    with open(tt_path, "wb") as f:
        f.truncate(tt_size)
    
    with open(tt_path, "r+b") as f:
        fd = f.fileno()
        trans_table = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)

    while True:
        command = input()
        parsed_command = parse_command(command)
        command_type = parsed_command[0]

        if command_type == 'uci':
            print("id name Karl's Sun\nid author Izy266\nuciok")
        elif command_type == 'isready':
            print("readyok")
        elif command_type == 'position':
            fen, moves = parsed_command[1], parsed_command[2]
            handle_position(fen, moves)
        elif command_type == 'go':
            params = parsed_command[1]
            handle_go(params)
        elif command_type == 'move':
            move_from, move_to, promo_piece = parsed_command[1], parsed_command[2], parsed_command[3]
            handle_move(move_from, move_to, promo_piece)
        elif command_type == 'stop':
            handle_stop()
        elif command_type == 'ucinewgame':
            handle_ucinewgame()
        elif command_type == 'quit':
            pool.close()
            pool.terminate()
            os.remove(tt_path)
            break
            
        print("Done")
