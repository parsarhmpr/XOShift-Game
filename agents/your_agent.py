from typing import List, Optional, Tuple
from agent_utils import get_all_valid_moves
from game import XOShiftGame

def agent_move(board: List[List[Optional[str]]], player_symbol: str) -> Tuple[int, int, int, int]:

    size = len(board)
    valid_moves = get_all_valid_moves(board, player_symbol)

    for move in valid_moves:
        new_board = simulate(board, move, player_symbol, size)
        if quick_check_winner(new_board, move[2], move[3], player_symbol, size):
            return move


    DEPTH = 4 if size==3 else 3
    score, best_move = minimax(board, player_symbol, DEPTH, float('-inf'), float('inf'), True, size)
    if best_move is None:
        return valid_moves[0] if valid_moves else (0, 0, 0, 0)
    return best_move


def simulate(board, move, symbol, size):

    b = [row.copy() for row in board]
    game = XOShiftGame(size = size)
    game.board = b
    (sr, sc, tr, tc) = move
    game.apply_move(sr, sc, tr, tc, symbol)
    return game.board

def quick_check_winner(board, tr, tc, player_symbol, size):

    if all(board[tr][x] == player_symbol for x in range(size)):
        return True

    elif all(board[x][tc] == player_symbol for x in range(size)):
        return True

    if tr == tc and all(board[x][x] == player_symbol for x in range(size)):
        return True

    if tr+tc == size-1 and all(board[x][size-1-x] == player_symbol for x in range(size)):
        return True

    return False

def check_winner(board):
    size = len(board)

    # checking rows
    for row in board:
        if row[0] is not None and all(cell == row[0] for cell in row):
            return row[0]

    # checking columns
    for col in range(size):
        if board[0][col] is not None and all(board[row][col] == board[0][col] for row in range(size)):
            return board[0][col]

    # checking main diameter
    if board[0][0] is not None and all(board[i][i] == board[0][0] for i in range(size)):
        return board[0][0]

    # checking minor diameter
    if board[0][size-1] is not None and all(board[i][size-1-i] == board[0][size-1] for i in range(size)):
        return board[0][size-1]

    # no one has won yet
    return None

def heuristic(board, player_symbol):
    opp = 'O' if player_symbol == 'X' else 'X'
    size = len(board)
    score = 0

    lines = []

    for i in range(size):
        lines.append([board[i][j] for j in range(size)])  # Row
        lines.append([board[j][i] for j in range(size)])  # Column

    lines.append([board[i][i] for i in range(size)])             # Main diagonal
    lines.append([board[i][size - 1 - i] for i in range(size)])  # Anti-diagonal

    for line in lines:
        if line.count(player_symbol) == size-1 and line.count(None) == 1:
            score += 10
        if line.count(opp) == size-1 and line.count(None) == 1:
            score -= 12
    return score

def minimax(
    board: List[List[Optional[str]]],
    player_symbol: str,
    depth: int,
    alpha: float,
    beta: float,
    maximizing_player: bool,
    size: int,
) -> Tuple[float, Optional[Tuple[int, int, int, int]]]:

    winner = check_winner(board)
    if winner == player_symbol:
        return float('inf'), None
    elif winner is not None:
        return float('-inf'), None
    if depth == 0:
        return heuristic(board, player_symbol), None


    current_symbol = player_symbol if maximizing_player else opponent(player_symbol)
    moves = get_all_valid_moves(board, current_symbol)
    if not moves:
        return heuristic(board, player_symbol), None

    # ---------- MOVE ORDERING ----------
    moves_boards_scores = []  # tuples: (move, maybe_new_board_or_None, score_for_ordering)

    # For each move: simulate once, compute full heuristic(new_board) and store new_board for reuse.
    for mv in moves:
        new_b = simulate(board, mv, current_symbol, size)
        score = heuristic(new_b, player_symbol)
        moves_boards_scores.append((mv, new_b, score))

    # sort: maximizing -> descending, minimizing -> ascending
    moves_boards_scores.sort(key=lambda x: x[2], reverse=maximizing_player)

    # ---------- main minimax loop (uses possibly precomputed new_board) ----------
    if maximizing_player:
        best_score = float('-inf')
        best_move = None
        for mv, new_b, _ in moves_boards_scores:
            score, _ = minimax(new_b, player_symbol, depth - 1, alpha, beta, False, size)
            if score > best_score:
                best_score = score
                best_move = mv
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        best_move = None
        for mv, new_b, _ in moves_boards_scores:
            score, _ = minimax(new_b, player_symbol, depth - 1, alpha, beta, True, size)
            if score < best_score:
                best_score = score
                best_move = mv
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

def opponent(player_symbol: str) -> str:
    return 'O' if player_symbol == 'X' else 'X'

def apply_shift_to_line(
    line: List[Optional[str]],
    src_idx: int,
    tgt_idx: int,
    player_symbol: str
)-> List[Optional[str]]:

    new_line = list(line)
    if src_idx < tgt_idx:
        for i in range(src_idx, tgt_idx):
             new_line[i] = line[i + 1]
        new_line[tgt_idx] = player_symbol
    else:
         for i in range(src_idx, tgt_idx, -1):
            new_line[i] = line[i - 1]
         new_line[tgt_idx] = player_symbol
    return new_line


#--------------------------------------------------------------------

#changing heuristic
#adding check winner to heuristic
#add check all winner for draw
#add quick sorting for pruning in 5*5

