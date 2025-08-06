import random
from typing import List, Optional, Tuple
from your_agent import agent_move, check_winner  # Your agent's file
from agent_utils import get_all_valid_moves

SIZE = 3  # or 3, 4 depending on your game
NUM_GAMES = 100


def create_board(size: int) -> List[List[Optional[str]]]:
    return [[None for _ in range(size)] for _ in range(size)]


def random_agent_move(board: List[List[Optional[str]]], player: str) -> Tuple[int, int, int, int]:
    moves = get_all_valid_moves(board, player)
    return random.choice(moves) if moves else (0, 0, 0, 0)


def apply_move(board: List[List[Optional[str]]], move: Tuple[int, int, int, int], player: str) -> None:
    sr, sc, tr, tc = move
    if sr == tr:
        if sc < tc:
            for i in range(sc, tc):
                board[sr][i] = board[sr][i + 1]
        else:
            for i in range(tc, sc):
                board[sr][i + 1] = board[sr][i]
    else:
        if sr < tr:
            for i in range(sr, tr):
                board[i][sc] = board[i + 1][sc]
        else:
            for i in range(tr, sr):
                board[i + 1][sc] = board[i][sc]
    board[tr][tc] = player


def play_game(agent_first: bool = True) -> Optional[str]:
    board = create_board(SIZE)
    player = 'X' if agent_first else 'O'
    opponent = 'O' if agent_first else 'X'

    for _ in range(SIZE * SIZE * 2):  # maximum moves before full board
        if get_all_valid_moves(board, player):
            if player == 'X':
                move = agent_move(board, player) if agent_first else random_agent_move(board, player)
            else:
                move = random_agent_move(board, player) if agent_first else agent_move(board, player)
            apply_move(board, move, player)
            winner = check_winner(board)
            if winner:
                return winner
        player = 'O' if player == 'X' else 'X'
    return None  # draw


def simulate_n_games(n: int) -> None:
    wins = 0
    losses = 0
    draws = 0
    for i in range(n):
        agent_first = (i % 2 == 0)
        winner = play_game(agent_first)
        if winner == 'X':
            if agent_first:
                wins += 1
            else:
                losses += 1
        elif winner == 'O':
            if agent_first:
                losses += 1
            else:
                wins += 1
        else:
            draws += 1
    print(f"Wins: {wins}, Losses: {losses}, Draws: {draws}, Win rate: {wins / n:.2%}")


if __name__ == "__main__":
    simulate_n_games(NUM_GAMES)
