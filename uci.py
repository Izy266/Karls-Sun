from engine import *
import multiprocessing as mp
import os

if __name__ == '__main__':
    ready = False
    game = GameState()
    cores = mp.cpu_count()//2 - 1
    pool = mp.Pool(processes=cores)
    tt_size = 1040000000 # bytes

    with open("t.dat", "wb") as f:
        f.truncate(tt_size)
    
    with open("t.dat", "r+b") as f:
        fd = f.fileno()
        trans_table = mmap.mmap(fd, 0, access=mmap.ACCESS_WRITE)

    ready = True
    def handle_uci(command, ready):
        ready = False
        print("id name karl\nid author Izy266\nuciok")
        ready = True

    def handle_isready(command, ready):
        if ready:
            print("readyok")
        else:
            print("Engine not ready")
    
    def handle_position(command, ready):
        ready = False
        moves_ind = command.index("moves") if "moves" in command else None
        fen = (
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"
            if "fen" not in command
            else command[command.index("fen") + 3 : moves_ind].strip()
        )
        game.build_fen(fen)

        if moves_ind:
            moves = command[moves_ind + 5 :].split()
            moves = [
                (game.parse_loc(move[:2]), game.parse_loc(move[2:])) for move in moves
            ]
            for move in moves:
                game.move(move)
        ready = True

    def handle_go(command, ready):
        ready = False
        go = command.split()[1:]
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

    def handle_move(command, ready):
        ready = False
        move = command.split()[1:]
        move = [int(i) for i in move]
        game.move((move[0], move[1]))
        ready = True
    
    def handle_stop(command, ready):
        trans_table[-1] = 1
    
    def handle_ucinewgame(command, ready):
        game.build_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -")

    command_dict = {
        "uci": handle_uci,
        "isready": handle_isready,
        "position": handle_position,
        "go": handle_go,
        "move": handle_move,
        "stop": handle_stop,
        "ucinewgame": handle_ucinewgame
    }

    ready = True
    while True:
        command = input().strip()
        print(f"COMMAND RECEIVED: {command}")
        command_type = command.split()[0]
        if command_type in command_dict:
            command_dict[command_type](command, ready)
        elif command_type == "quit":
            pool.terminate()
            os.remove("t.dat")
            break
        else:
            print(f"Unknown command: {command}")