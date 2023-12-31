# Karl's Sun (~ 2600 Elo)
![karls sun logo 2](https://github.com/Izy266/Karls-Sun/assets/54121657/be459530-f7e5-4bf6-adcd-00ab63216af5)

Karl's Sun is a multi-threaded Python-based chess engine designed for playing chess games, analyzing positions, and providing a challenging opponent for players. The engine utilizes a combination of classic chess algorithms, board representation techniques, and modern enhancements for efficient move generation and evaluation.

## Features:

### General:
* UCI Protocol Support: Karl's Sun follows the Universal Chess Interface (UCI) protocol, allowing seamless integration with various chess interfaces and applications.

### Evaluation:
* **Opening Book**: Karl's Sun utilizes the komodo.bin opening book, an opening book used by the Komodo chess engine, created by the opening book expert Erdogan Gunes
* **PeSTO Board Evaluation**: A Piece-Square Tables Only (PeSTO) evaluation function, developed by Ronald Friederich for his chess engine RofChade, that performs a tapered evaluation to interpolate between piece-square tables values for the opening and endgame.
* **Negamax Framework**: A decision-making algorithm used in game theory and artificial intelligence for two-player zero-sum games that finds the best move by recursively exploring the game tree with minimax principles.
* **Quiescence Search**: Explores tactical sequences such as captures and promotions to completion until the board state is quiet to limit the horizon effect.
* **Syzygy Endgame Tablebases**: The engine incorporates Syzygy endgame tablebases for positions with up to 4 pieces, enabling precise endgame play.

### Efficiencies:
* **Lazy SMP Multi-Threading**: The engine uses the parallel search approach lazy SMP, sharing a transposition table across all cores, accelerating the search process and resulting in better engine moves.
* **Iterative Deepening with MTD(f)**: Karl's Sun employs the MTD(f) (Memory-enhanced Test Driver with a fixed-depth window) search algorithm in conjunction with iterative deepening. This approach amalgamates the advantages of binary search and memory enhancements to efficiently identify the optimal move.
* **Transposition Table**: Karl's Sun uses a transposition table to store and retrieve previously computed positions, optimizing search performance.
* **Bitwise Operations**: While the boardstate is stored as a one dimensional array, bitwise operations are used to traverse the board when possible, improving efficiency when generating legal moves.
* **Zobrist Hashing**: Transforms the board position of arbitrary size into a 64 bit integer for efficient storage and faster lookups

### Move Ordering:
* **MVV_LVA(Most Valuable Victim - Least Valuable Attacker)**: Prioritizes capturing moves based on the value of the victim and attacker pieces, enhancing move ordering of captures.
* **Killer Heuristic**: The engine prioritizes moves that were successful in previous iterations at the same depth, improving chances of obtaining cutoffs early, enhancing search efficiency.
* **Relative History Heuristic**: Karl's Sun utilizes a relative history heuristic to prioritize moves that have historically led to cutoffs in relation to the move's frequency during the search.
* **Countermove Heuristic**: The engine increases the value of moves that caused a cutoff in response to specific moves played during the search, ordering it earlier.

### Pruning:
* **Null Move Reduction**: Reduces the search tree by four plies if null move is played, i.e turn is passed, and a reduced search resulted in a beta cuttoff. The ply reduction rather than the complete pruning of the tree makes the technique less vulnerable to Zugzwang, thus more reliable in the endgame.
* **Extended Futility Pruning**: Prunes search tree if material balance + a futility margin is less than alpha, indicating the current branch has little to no hope in improving the position.
* **Reverse Futility Pruning**: Prunes search tree if lazy evaluation - a futility margin is greater than or equal to beta.
* **Delta Pruning**: Similar to extended futility pruning but done exclusively in quiescence search with the futility margin being the largest possible positional swing, i.e. the value of a queen.
* **SEE(Static Exchange Evaluation)**: Used to assess the value of captures in a position, allowing the engine to determine the feasibility and desirability of capturing moves. Moves with a negative SEE are skipped in the Quiescense search.
* **Late Move Reduction**: Late Move Reduction is employed to dynamically adjust the search depth for moves occurring later in the move list, with the odds of those moves improving the position being slim due to quality move ordering.

### Extensions:
* **Mate Threat Extension**: If a potential checkmate threat is detected when the null move is made, the search is deepened to explore lines that address and potentially counteract the mate threat.
* **Check Extension**: This extension is triggered when a king is in check, leading to improved checkmate evasion capabilities and a more efficient search for checkmate opportunities.
* **One Reply Extension**: If there is only one legal move in a position, the search tree is extended, as it would not result in a massive tree extension while allowing the engine to gain a more accurate assessment of the resulting position.
  
Getting Started:

Install dependencies:

    pip install -r requirements.txt

For UCI support:
1. Open the `karls_sun.py` file.
2. Locate line 4 and replace the existing code between the quotations with the following: `pypy` or `python` followed by the full path to `uci.py`.
3. Convert `karls_sun.py` to an executable using `pyinstaller` or any other py to exe converter.
4. Add the newly created executable to any GUI that supports the UCI protocol, such as Lucas or Arena.
