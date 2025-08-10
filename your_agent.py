from typing import List, Optional, Tuple
from copy import deepcopy
import random
from agent_utils import get_all_valid_moves
from game import XOShiftGame

def agent_move(board: List[List[Optional[str]]], player_symbol: str) -> Tuple[int, int, int, int]:


    size = len(board)
    DEPTH = 3 if size==3 else 4
    score, best_move = minimax(board, player_symbol, DEPTH, float('-inf'), float('inf'), True, size)
    if best_move is None:
        valid_moves = get_all_valid_moves(board, player_symbol)
        return valid_moves[0] if valid_moves else (0, 0, 0, 0)
    return best_move


def simulate(board, move, symbol, size):

    b = deepcopy(board)
    game = XOShiftGame(size = size)
    game.board = b
    (sr, sc, tr, tc) = move
    game.apply_move(sr, sc, tr, tc, symbol)
    return game.board

def is_winning_move(board, move, symbol, size):

    b2 = simulate(board, move, symbol, size)
    game = XOShiftGame(size = size)
    game.board = b2
    return game.check_winner() == symbol


def check_winner(board):
    size = len(board)

    # بررسی سطرها
    for row in board:
        if row[0] is not None and all(cell == row[0] for cell in row):
            return row[0]

    # بررسی ستون‌ها
    for col in range(size):
        if board[0][col] is not None and all(board[row][col] == board[0][col] for row in range(size)):
            return board[0][col]

    # بررسی قطر اصلی
    if board[0][0] is not None and all(board[i][i] == board[0][0] for i in range(size)):
        return board[0][0]

    # بررسی قطر فرعی
    if board[0][size-1] is not None and all(board[i][size-1-i] == board[0][size-1] for i in range(size)):
        return board[0][size-1]

    # برنده‌ای وجود ندارد
    return None

def check_all_winners(board):
    """
    برمی‌گرداند لیستی از همه بازیکن‌هایی که حداقل یک خط کامل دارند.
    اگر لیست خالی باشد یعنی هیچ کس برنده نیست.
    """
    size = len(board)
    winners = set()

    # بررسی سطرها
    for row in board:
        if row[0] is not None and all(cell == row[0] for cell in row):
            winners.add(row[0])

    # بررسی ستون‌ها
    for col in range(size):
        if board[0][col] is not None and all(board[row][col] == board[0][col] for row in range(size)):
            winners.add(board[0][col])

    # بررسی قطر اصلی
    if board[0][0] is not None and all(board[i][i] == board[0][0] for i in range(size)):
        winners.add(board[0][0])

    # بررسی قطر فرعی
    if board[0][size - 1] is not None and all(board[i][size - 1 - i] == board[0][size - 1] for i in range(size)):
        winners.add(board[0][size - 1])

    return list(winners)


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
    size: int
) -> Tuple[float, Optional[Tuple[int, int, int, int]]]:

    winner = check_winner(board)
    if winner == player_symbol:
        return float('inf'), None
    elif winner is not None:
        return float('-inf'), None

    if depth == 0:
        return heuristic(board, player_symbol), None

    if maximizing_player:
        best_score = float('-inf')
        best_move = None
        moves = get_all_valid_moves(board, player_symbol)

        # Optional: مرتب‌سازی حرکات (move ordering) براساس یک ارزیابی سریع
        # moves.sort(key=lambda mv: quick_eval_after_move(board, mv, player_symbol, size), reverse=True)

        for move in moves:
            new_board = simulate(board, move, player_symbol, size)
            score, _ = minimax(new_board, player_symbol, depth - 1, alpha, beta, False, size)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break  # β-cutoff (prune)
        return best_score, best_move

    else:
        opp = 'O' if player_symbol is 'X' else 'X'
        best_score = float('inf')
        best_move = None
        moves = get_all_valid_moves(board, opp)

        # Optional: مرتب‌سازی حرکات برای حریف (کم‌ترین امتیاز اول)
        # moves.sort(key=lambda mv: quick_eval_after_move(board, mv, opp, size))

        for move in moves:
            new_board = simulate(board, move, opp, size)
            score, _ = minimax(new_board, player_symbol, depth - 1, alpha, beta, True, size)
            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # α-cutoff (prune)
        # 18
        return best_score, best_move

    #اضافه کردن check win  به هیوریستیک