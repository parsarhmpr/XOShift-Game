from typing import List, Optional, Tuple
from copy import deepcopy
import random
from agent_utils import get_all_valid_moves
from game import XOShiftGame

def agent_move(board: List[List[Optional[str]]], player_symbol: str) -> Tuple[int, int, int, int]:

    valid_moves = get_all_valid_moves(board, player_symbol)
    if not valid_moves:
        return 0, 0, 0, 0

    opponent_symbol = 'O' if player_symbol == 'X' else 'X'
    size = len(board)


    for move in valid_moves:
        if _is_winning_move(board, move, player_symbol, size):
            return move

    for move in valid_moves:
        b2 = _simulate(board, move, player_symbol, size)
        opp_moves = get_all_valid_moves(b2, opponent_symbol)
        if any(_is_winning_move(b2, opp_move, opponent_symbol, size) for opp_move in opp_moves):
            continue
        return move


    best_move = None
    best_score = float('-inf')
    for move in valid_moves:
        b2 = _simulate(board, move, player_symbol, size)
        score = _heuristic(b2, player_symbol)
        if score > best_score:
            best_score, best_move = score, move

    if best_move:
        return best_move


    return random.choice(valid_moves)


def _simulate(board, move, symbol, size):

    b = deepcopy(board)
    game = XOShiftGame(size=size)
    game.board = b
    sr, sc, tr, tc= move
    game.apply_move(sr, sc, tr, tc, symbol)
    return game.board

def _is_winning_move(board, move, symbol, size):

    b2 = _simulate(board, move, symbol, size)
    game = XOShiftGame(size=size)
    game.board = b2
    return game.check_winner() == symbol

def _heuristic(board, symbol):

    opp = 'O' if symbol == 'X' else 'X'
    size = len(board)
    score = 0

    lines = []


    for i in range(size):
        lines.append([board[i][j] for j in range(size)])
        lines.append([board[j][i] for j in range(size)])

    lines.append([board[i][i] for i in range(size)])
    lines.append([board[i][size-1-i] for i in range(size)])

    for line in lines:
        if line.count(symbol) == size - 1 and line.count(None) == 1:
            score += 3
        if line.count(opp) == size - 1 and line.count(None) == 1:
            score -= 4

    return score

