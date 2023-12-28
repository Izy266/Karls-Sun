data_size = 13 # bytes
INFINITY = 15000

def extract_components(data):
    move_to = data & 0x7f
    move_from = (data >> 7) & 0x3F
    depth = (data >> 13) & 0x3F
    flag = (data >> 19) & 0x3
    score = (data >> 21) & 0xFFFF
    hash_key = (data >> 37) & 0xFFFFFFFFFFFFFFFF
    return hash_key, score, flag, depth, move_from, move_to

def verify_tt(data, key):
    hash_key, score, flag, depth, move_from, move_to = extract_components(data)
    data = (score & 0xFFFF) << 21 | (flag & 0x3) << 19 | (depth & 0x3F) << 13 | (move_from & 0x3F) << 7 | move_to & 0x7f
    return [score, flag, depth, (move_from, move_to)] if hash_key ^ data == key else False

def store_tt(tt, hash_key, score, flag, depth, move):
    tt_size = len(tt) - 520 # using final ~0.5kb for other info
    move_from, move_to = move
    score = score + INFINITY + 1
    data = (score & 0xFFFF) << 21 | (flag & 0x3) << 19 | (depth & 0x3F) << 13 | (move_from & 0x3F) << 7 | move_to & 0x7f
    data = ((hash_key ^ data) & 0xFFFFFFFFFFFFFFFF) << 37 | (score & 0xFFFF) << 21 | (flag & 0x3) << 19 | (depth & 0x3F) << 13 | (move_from & 0x3F) << 7 | move_to & 0x7f
    data_bytes = data.to_bytes(data_size, byteorder='little')
    byte_start = (hash_key % (tt_size//data_size)) 
    tt[byte_start:byte_start + data_size] = data_bytes

def get_tt(tt, hash_key):
    tt_size = len(tt) - 520 # using final ~0.5kb for other info
    byte_start = (hash_key % (tt_size//data_size))
    byte_end = byte_start + data_size
    extracted_data_bytes = tt[byte_start:byte_end]
    extracted_data = int.from_bytes(extracted_data_bytes, byteorder='little')
    data = verify_tt(extracted_data, hash_key)
    if data:
        data[0] -= (INFINITY + 1)
        return data
    else:
        return None
        
def set_best(tt, score, move, depth):
    ind = (depth - 1) * 4
    byte_start = len(tt) - 520 + ind
    score += INFINITY + 1
    score_bytes = score.to_bytes(2, byteorder='little')
    tt[byte_start:byte_start+2] = score_bytes 
    tt[byte_start+2] = move[0]
    tt[byte_start+3] = move[1]

def get_best(tt, ind = -1):
    depth = ind if ind > 0 else 100
    best = []
    for i in range(depth):
        off = i * 4
        byte_start = len(tt) - 520 + off
        score_bytes = tt[byte_start:byte_start+2]
        score = int.from_bytes(score_bytes, byteorder='little') - INFINITY - 1
        move = (tt[byte_start+2], tt[byte_start+3])
        if move != (0, 0):
            best.append((score, move, i + 1))
            if score > 14000:
                break
    ind = max(-len(best), ind)
    return best[-1] if ind > 0 else best[ind]

def clear_best(tt):
    byte_start = len(tt) - 520
    for i in range(400):
        tt[byte_start + i] = 0

def node_count(tt, arg):
    byte_start = len(tt) - 120 + 5
    node_bytes = tt[byte_start:byte_start+4]
    node_count = int.from_bytes(node_bytes, byteorder='little')
    if arg == "get":
        return node_count
    if arg == "add":
        node_count += 1
    elif arg == "clear":
        node_count = 0
    node_bytes = node_count.to_bytes(4, byteorder='little')
    tt[byte_start:byte_start+4] = node_bytes

def set_time(tt, time, arg):
    off = 9 if arg == "max" else 11
    byte_start = len(tt) - 120 + off
    byte_len = 2 if arg == "max" else 6 
    time_bytes = time.to_bytes(byte_len, byteorder='little')
    tt[byte_start:byte_start+byte_len] = time_bytes

def get_time(tt, arg):
    off = 9 if arg == "max" else 11
    byte_start = len(tt) - 120 + off
    byte_len = 2 if arg == "max" else 6 
    time_bytes = tt[byte_start:byte_start+byte_len]
    time = int.from_bytes(time_bytes, byteorder='little')
    return time

def depth_reach(tt, arg, depth = None):
    byte_start = len(tt) - 103
    byte_len = 2
    if arg == "set":
        depth_bytes = depth.to_bytes(byte_len, byteorder='little')
        tt[byte_start:byte_start + byte_len] = depth_bytes
    else:
        depth_bytes = tt[byte_start:byte_start + byte_len]
        depth = int.from_bytes(depth_bytes, byteorder='little')
        return depth
