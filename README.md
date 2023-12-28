# Karl Chess (~ 2500 Elo)

Karl Chess is a multi-threaded Python-based chess engine designed for playing chess games, analyzing positions, and providing a challenging opponent for players. The engine utilizes a combination of classic chess algorithms, board representation techniques, and modern enhancements for efficient move generation and evaluation.

## Features:

### General:
* UCI Protocol Support: KarlPy follows the Universal Chess Interface (UCI) protocol, allowing seamless integration with various chess interfaces and applications.

### Evaluation:
* **Opening Book**: Karl Chess utilizes the komodo.bin opening book, an opening book used by the Komodo chess engine, created by the opening book expert Erdogan Gunes
* **PeSTO Board Evaluation**: This is a Piece-Square Tables Only (PeSTO) evaluation function used in chess engines. It was developed by Ronald Friederich for his chess engine RofChade and further used in his experimental chess engine PeSTO[^1^][1]. The PeSTO evaluation function performs a tapered evaluation to interpolate between piece-square tables values for the opening and endgame, optimized by Texel's tuning method[^1^][1]. It's intended to replace Tomasz Michniewski's Simplified Evaluation Function and has been successfully applied in several engines[^1^][1]. The PeSTO evaluation function is known for its efficiency and effectiveness in evaluating board positions in chess[^1^][1].
* **Negamax Framework**: This is a decision-making algorithm used in game theory and artificial intelligence for two-player zero-sum games. The principle of Negamax is that the value of a position for one player is the negation of the value for the other player, based on the zero-sum property. The Negamax algorithm simplifies the implementation of the minimax algorithm by using a single procedure to evaluate positions for both players, which is a significant advantage over the minimax algorithm.
* **Iterative Deepening with MTD(f)**: Karl Chess employs the MTD(f) (Memory-enhanced Test Driver with a fixed-depth window) search algorithm in conjunction with iterative deepening. This approach amalgamates the advantages of binary search and memory enhancements to efficiently identify the optimal move.
* **Syzygy Endgame Tablebases**: The engine incorporates Syzygy endgame tablebases for positions with up to 4 pieces, enabling precise endgame play.


### Pruning:







* Transposition Table: Karl Chess uses a transposition table to store and retrieve previously computed positions, optimizing search performance.

* Move Ordering: Efficient move ordering techniques, including killer moves and history heuristics, contribute to a more focused search and improved gameplay.

* Material and Positional Evaluation: The evaluation function combines material balance and positional considerations to assess the strength of positions and guide move selection.

* Multi-Threading: The engine uses the parallel search approach lazy SMP for parallel processing, accelerating the search process and resulting in better engine moves.

Getting Started:

Clone the repository:

    git clone https://github.com/yourusername/karlpy-chess-engine.git

Install dependencies:

    pip install -r requirements.txt

Contributions:

Contributions, bug reports, and feature requests are welcome! Feel free to submit pull requests or open issues to help improve KarlPy.
License:

This project is licensed under the MIT License - see the LICENSE file for details.

Adjust the content as needed, and include relevant links to your repository, license file, and any additional documentation or resources.
