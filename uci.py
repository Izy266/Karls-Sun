import re
import multiprocessing as mp
from engine import *

def parse_command(command):
    uci_pattern = re.compile(r'^uci$')
    isready_pattern = re.compile(r'^isready$')
    position_pattern = re.compile(r'^position\s+(startpos|fen\s+(.*?))(\s+moves\s+(.*))?$')
    go_pattern = re.compile(r'^go\s+(.*)$')
    move_pattern = re.compile(r'^move\s+(\d+)\s+(\d+)$')
    stop_pattern = re.compile(r'^stop$')
    ucinewgame_pattern = re.compile(r'^ucinewgame$')
    
    if uci_pattern.match(command):
        return 'uci'
    elif isready_pattern.match(command):
        return 'isready'
    elif position_match := position_pattern.match(command):
        fen = position_match.group(2) if position_match.group(2) else 'startpos'
        moves = position_match.group(4)
        return 'position', fen, moves
    elif go_match := go_pattern.match(command):
        params = go_match.group(1)
        return 'go', params
    elif move_match := move_pattern.match(command):
        move_from = int(move_match.group(1))
        move_to = int(move_match.group(2))
        return 'move', move_from, move_to
    elif stop_pattern.match(command):
        return 'stop'
    elif ucinewgame_pattern.match(command):
        return 'ucinewgame'
    else:
        return 'unknown'

def handle_go(params, ready):
    ready = False
    go = params.split()
    start_time = round(time.time()*1000)
    set_time(trans_table, start_time, "start")
    node_count(trans_table, "clear")
    clear_best(trans_table)
    depth_reach(trans_table, "set", 0)
    trans_table[-1] = 0
    if "depth" in go:
        max_time, max_depth = 65000, int(go[go.index("depth") + 1])
        set_time(trans_table, max_time, "max")
        args = [(game, max_depth) for _ in range(cores)]
        pool.map(get_move, args)
        score, move, depth = get_best(trans_table)
        game.move(move)
        print(move)
    elif "movetime" in go:
        max_time = int(go[go.index("movetime") + 1])
        set_time(trans_table, max_time, "max")
        max_depth = 100
        args = [(game, max_depth) for _ in range(cores)]
        pool.map(get_move, args)
        score, move, depth = get_best(trans_table) if get_best(trans_table)[-1] < depth_reach(trans_table, "get") else get_best(trans_table, -2)
        game.move(move)
        print(move)
    ready = True

def handle_uci(ready):
    ready = False
    print("id name karl\nid author Izy266\nuciok")
    ready = True

def handle_isready(ready):
    if ready:
        print("readyok")
    else:
        print("Engine not ready")

def handle_position(fen, moves, ready):
    ready = False
    game.build_fen(fen)

    if moves:
        moves = [
            (game.parse_loc(move[:2]), game.parse_loc(move[2:])) for move in moves.split()
        ]
        for move in moves:
            game.move(move)
    ready = True

def handle_move(move_from, move_to, ready):
    ready = False
    game.move((move_from, move_to))
    ready = True

def handle_stop(ready):
    trans_table[-1] = 1

def handle_ucinewgame(ready):
    game.build_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -")

if __name__ == '__main__':
    ready = False
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

    ready = True
    while True:
        command = input().strip()
        print(f"COMMAND RECEIVED: {command}")
        parsed_command = parse_command(command)
        command_type = parsed_command[0]

        if command_type == 'uci':
            handle_uci(command, ready)
        elif command_type == 'isready':
            handle_isready(command, ready)
        elif command_type == 'position':
            fen, moves = parsed_command[1], parsed_command[2]
            handle_position(fen, moves, ready)
        elif command_type == 'go':
            params = parsed_command[1]
            handle_go(params, ready)
        elif command_type == 'move':
            move_from, move_to = parsed_command[1], parsed_command[2]
            handle_move(move_from, move_to, ready)
        elif command_type == 'stop':
            handle_stop(command, ready)
        elif command_type == 'ucinewgame':
            handle_ucinewgame(command, ready)
        elif command_type == 'quit':
            pool.close()
            pool.terminate()
            os.remove("t.dat")
            break
        else:
            print(f"Unknown command: {command}")
