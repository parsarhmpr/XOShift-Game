import datetime
import json
import multiprocessing
import os
import queue
import sys
from typing import Optional, Callable, List, Dict, Any

import pygame

from agent_loader import load_agent
from game import XOShiftGame
from ui import XOShiftUI, REPLAYS_DIR

AGENT_TIME_LIMIT = 5.0
MAX_TURNS = 250
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 850


def agent_process_wrapper(agent_path: str,
                          board_copy: List[List[Optional[str]]],
                          player_symbol: str,
                          result_queue: multiprocessing.Queue):
    """
    Child process target: load the agent module by its file path,
    call its agent_move(), and send back the result (or exception).
    """
    try:
        agent_move = load_agent(agent_path)
        move = agent_move(board_copy, player_symbol)
        result_queue.put(("move", move))
    except Exception as e:
        result_queue.put(("error", e))


def _apply_replay_moves_to_index(game_instance: XOShiftGame,
                                 moves: List[Dict[str, Any]],
                                 target_move_count: int):
    # Reset the board
    board_size = game_instance.size
    game_instance.board = [[game_instance.EMPTY] * board_size for _ in range(board_size)]
    game_instance.winner = None
    game_instance.winning_line_coords = None
    game_instance.current_player_index = 0

    for i in range(min(target_move_count, len(moves))):
        move_data = moves[i]
        p = move_data.get("player")
        sr, sc = move_data.get("src_r"), move_data.get("src_c")
        tr, tc = move_data.get("tgt_r"), move_data.get("tgt_c")
        if None in (p, sr, sc, tr, tc):
            print(f"Replay Warning: Move {i+1} incomplete; skipping.")
            continue
        try:
            game_instance.current_player_index = game_instance.PLAYERS.index(p)
        except ValueError:
            print(f"Replay Warning: Unknown player '{p}' in move {i+1}; skipping.")
            continue
        success = game_instance.apply_move(sr, sc, tr, tc, p)
        if not success:
            print(f"Replay Warning: Move {i+1} invalid; skipping.")
        if not game_instance.winner:
            game_instance.switch_player()


def main_loop():
    pygame.init()
    multiprocessing.freeze_support()

    # Ensure replays folder
    if not os.path.exists(REPLAYS_DIR):
        os.makedirs(REPLAYS_DIR, exist_ok=True)

    screen = pygame.display.set_mode((SCREEN_WIDTH - 100, SCREEN_HEIGHT - 250))
    pygame.display.set_caption("XOShift Game")
    clock = pygame.time.Clock()

    ui = XOShiftUI(screen)
    game: Optional[XOShiftGame] = None

    # Always keep these as paths
    agent1_path = "your_agent.py"
    agent2_path = "sample_agent.py"

    current_moves: List[Dict[str, Any]] = []
    record_replay = False
    turn_count = 0

    loaded_replay: List[Dict[str, Any]] = []
    replay_index = 0
    replay_file: Optional[str] = None

    running = True
    while running:
        # Force draw if too many turns
        if game and not game.winner and turn_count >= MAX_TURNS:
            game.winner = "Draw"
            ui.state = XOShiftUI.STATE_GAME_OVER
            print(f"Draw at {MAX_TURNS} turns.")

        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                running = False
        if not running:
            break

        # Single UI event
        ui_ev = pygame.event.Event(pygame.NOEVENT)
        md = [e for e in events if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1]
        kd = [e for e in events if e.type == pygame.KEYDOWN]
        if md:
            ui_ev = md[0]
        elif kd:
            ui_ev = kd[0]

        action = ui.handle_event(ui_ev)
        if action:
            act = action["action"]

            # Quit
            if act == "quit":
                running = False

            # Start a new game
            elif act == "start_game":
                size = action["size"]
                mode = action["mode"]
                record_replay = action.get("record_replay", False) and mode != "replay-select-file"

                try:
                    game = XOShiftGame(size=size)
                except ValueError as e:
                    print(f"Init error: {e}")
                    ui.set_game(None)
                    continue

                turn_count = 0
                x_name = os.path.basename(agent1_path)[:-3]
                o_name = os.path.basename(agent2_path)[:-3]
                if mode == "human-human":
                    ui.player_types = {'X': 'human', 'O': 'human'}
                elif mode == "human-agent":
                    ui.player_types = {'X': 'human', 'O': o_name}
                elif mode == "agent-agent":
                    ui.player_types = {'X': x_name, 'O': o_name}

                ui.set_game(game)
                current_moves = []
                ui.replay_finished = False
                ui.state = (XOShiftUI.STATE_WAITING if mode == "agent-agent"
                            else XOShiftUI.STATE_SELECT)

            # Load a replay file
            elif act == "load_replay":
                replay_file = action["filename"]
                path = os.path.join(REPLAYS_DIR, replay_file)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        loaded_replay = data
                    else:
                        loaded_replay = data.get("moves", [])
                    if not loaded_replay:
                        raise ValueError("No moves")
                    board_sz = loaded_replay[0].get("board_size", ui.selected_board_size)
                    game = XOShiftGame(size=board_sz)
                    ui.player_types = {'X': 'Player 1', 'O': 'Player 2'}
                    ui.set_game(game)
                    ui.state = XOShiftUI.STATE_REPLAY
                    replay_index = 0
                    ui.replay_finished = False
                    _apply_replay_moves_to_index(game, loaded_replay, 0)
                except Exception as e:
                    print(f"Load replay error: {e}")
                    ui.set_game(None)

            # Apply a human move
            elif act == "apply_move" and game and ui.state != XOShiftUI.STATE_WAITING:
                sr, sc, tr, tc = action["move"]
                player = game.current_player
                if game.apply_move(sr, sc, tr, tc, player):
                    turn_count += 1
                    if record_replay:
                        current_moves.append({
                            "player": player, "src_r": sr, "src_c": sc,
                            "tgt_r": tr, "tgt_c": tc
                        })
                    if not game.winner:
                        game.switch_player()
                        human_next = (ui.selected_mode == "human-agent" and
                                      game.current_player_index == 1)
                        ui.state = (XOShiftUI.STATE_SELECT if human_next
                                    else XOShiftUI.STATE_WAITING)
                    else:
                        ui.state = XOShiftUI.STATE_GAME_OVER
                else:
                    print("Invalid human move")

            # Return to menu from in‐game
            elif act == "return_to_menu_ingame":
                game = None
                ui.set_game(None)
                current_moves = []
                loaded_replay = []
                replay_file = None

            # Return to menu after game over
            elif act == "return_to_menu":
                if game and ui.state == XOShiftUI.STATE_GAME_OVER and record_replay and current_moves:
                    mode_str = ui.selected_mode.replace("human", "H")\
                                               .replace("agent", "A")\
                                               .replace("-vs-", "-")
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    fname = f"xo_{game.size}x{game.size}_{mode_str}_{ts}.json"
                    p = os.path.join(REPLAYS_DIR, fname)
                    meta = {
                        "board_size": game.size,
                        "game_mode": ui.selected_mode,
                        "player_x_type": ui.player_types['X'],
                        "player_o_type": ui.player_types['O'],
                        "winner": game.winner
                    }
                    replay_data = {"metadata": meta, "moves": current_moves}
                    try:
                        with open(p, "w") as f:
                            json.dump(replay_data, f, indent=4)
                        print("Saved replay:", p)
                    except Exception as e:
                        print("Save error:", e)
                game = None
                ui.set_game(None)
                current_moves = []
                loaded_replay = []
                replay_file = None

            # Replay again
            elif act == "replay_again" and game and loaded_replay:
                ui.state = XOShiftUI.STATE_REPLAY
                replay_index = 0
                ui.replay_finished = False
                _apply_replay_moves_to_index(game, loaded_replay, 0)

        # Agent‐turn logic
        if game and not game.winner and ui.state == XOShiftUI.STATE_WAITING:
            # Decide which path to use
            if ui.selected_mode == "human-agent" and game.current_player_index == 1:
                agent_path = agent2_path
            elif ui.selected_mode == "agent-agent":
                agent_path = (agent1_path if game.current_player_index == 0
                              else agent2_path)
            else:
                agent_path = None

            if agent_path:
                ui.draw()
                pygame.display.flip()

                board_copy = [row[:] for row in game.board]
                q = multiprocessing.Queue()
                proc = multiprocessing.Process(
                    target=agent_process_wrapper,
                    args=(agent_path, board_copy, game.current_player, q)
                )
                proc.start()

                agent_coords = None
                try:
                    kind, payload = q.get(timeout=AGENT_TIME_LIMIT)
                    if kind == "move":
                        agent_coords = payload
                    else:
                        print("Agent error:", payload)
                except queue.Empty:
                    print("Agent timed out")

                # Clean up
                if proc.is_alive():
                    proc.terminate()
                    proc.join(0.5)

                if agent_coords:
                    sr, sc, tr, tc = agent_coords
                    if game.apply_move(sr, sc, tr, tc, game.current_player):
                        turn_count += 1
                        if record_replay:
                            current_moves.append({
                                "player": game.current_player,
                                "src_r": sr, "src_c": sc,
                                "tgt_r": tr, "tgt_c": tc
                            })
                        if not game.winner:
                            game.switch_player()
                    else:
                        print("Agent made invalid move")
                        game.switch_player()
                else:
                    # no coords → skip
                    game.switch_player()

                # Advance state
                if game.winner:
                    ui.state = XOShiftUI.STATE_GAME_OVER
                else:
                    human_next = (ui.selected_mode == "human-agent" and
                                  game.current_player_index == 1)
                    ui.state = (XOShiftUI.STATE_SELECT if human_next
                                else XOShiftUI.STATE_WAITING)

        # Replay navigation
        if ui.state == XOShiftUI.STATE_REPLAY and game and not ui.replay_finished:
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RIGHT and replay_index < len(loaded_replay):
                        replay_index += 1
                        _apply_replay_moves_to_index(game, loaded_replay, replay_index)
                        if replay_index == len(loaded_replay):
                            ui.replay_finished = True
                    elif ev.key == pygame.K_LEFT and replay_index > 0:
                        replay_index -= 1
                        _apply_replay_moves_to_index(game, loaded_replay, replay_index)
                        ui.replay_finished = False
                    break

        # Final draw
        ui.draw()
        clock.tick(30)

    # On quit, save final game if needed
    if game and game.winner and record_replay and current_moves:
        mode_str = ui.selected_mode.replace("human", "H")\
                                   .replace("agent", "A")\
                                   .replace("-vs-", "-")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"xo_{game.size}x{game.size}_{mode_str}_{ts}.json"
        p = os.path.join(REPLAYS_DIR, fname)
        meta = {
            "board_size": game.size,
            "game_mode": ui.selected_mode,
            "player_x_type": ui.player_types['X'],
            "player_o_type": ui.player_types['O'],
            "winner": game.winner
        }
        data = {"metadata": meta, "moves": current_moves}
        try:
            with open(p, "w") as f:
                json.dump(data, f, indent=4)
            print("Saved final replay:", p)
        except Exception as e:
            print("Final save error:", e)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_loop()
