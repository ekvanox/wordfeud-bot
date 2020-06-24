#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import heapq
import inspect
import logging
import os
import random
import time
import urllib
import sys

import coloredlogs
import requests
import urllib3
from emoji import UNICODE_EMOJI

try:    # Usually works
    from wordfeud_logic.board import Board
    from wordfeud_logic.wordlist import Wordlist
except ImportError:  # Needed for tests to run
    from wordfeudbot.wordfeud_logic.board import Board
    from wordfeudbot.wordfeud_logic.wordlist import Wordlist


class Wordfeud:
    def login(self, user_id: int, password: str, language_code: str):
        """Returns sessionid cookie used for future requests

        Args:
            user_id (int): Unique user id
            password (str): Previously randomly generated password
            language_code (str): Code for UI language: en,sv,no...

        Raises:
            Exception: Server not accepting credentials

        Returns:
            str: sessionid
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "90",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }

        data = f'{{"id": {user_id}, "password": "{password}", "language_code": "{language_code}"}}'

        response = requests.post(
            "https://api.wordfeud.com/wf/user/login/id/",
            headers=headers,
            data=data.encode("utf-8"),
            verify=VERIFY_SSL,
        )

        # Verify that server accepted credentials
        if response.json()["status"] == "error":
            raise Exception("Server returned error message")

        # Make cookies into a dictionary
        cookies = response.cookies.get_dict()

        # Return sessionid
        sessionid = cookies["sessionid"]
        return sessionid

    def board_and_tile_data(self, game_id=None):
        """Get info about users active games

        Returns:
            dict: Active games info
        """
        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        if game_id is None:
            # Data about all games
            response = requests.get(
                f"https://api.wordfeud.com/wf/user/games/detail/?known_tile_points=&known_boards=",
                headers=headers,
                verify=VERIFY_SSL,
            )
        else:
            # Data about specific game
            response = requests.get(
                f"https://api.wordfeud.com/wf/games/{game_id}/?known_tile_points=&known_boards=",
                headers=headers,
                verify=VERIFY_SSL,
            )

        parsed = response.json()
        return parsed

    def update_board_quarters(self, board_list):
        self.board_quarters = {}
        multiplier_number_to_text_dict = {
            0: "--", 1: "2l", 2: "3l", 3: "2w", 4: "3w"}

        default_board_placements = [
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
            "-- -- -- -- -- -- -- -- -- -- -- -- -- -- --",
        ]
        for board in board_list:
            board_id = board["board_id"]

            board_placements = default_board_placements
            board_placements = [row.split(" ") for row in board_placements]

            for row in range(len(board["board"])):
                for column in range(len(board["board"][row])):
                    multiplier_value_int = board["board"][row][column]
                    board_placements[row][column] = multiplier_number_to_text_dict[
                        multiplier_value_int
                    ]

            self.board_quarters[board_id] = board_placements

    def place_tiles(self, game: object, word: str, tile_positions: list):
        """Sends request to wordfeud servers to play a move

        Args:
            game (object): Game object with info about game id
            word (str): The full word that is going to be placed
            tile_positions (list): 2D list of all tiles and their respective positions

        Returns:
            dict: Server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = f"""{{"words": ["{word.upper()}"], "ruleset": {game.ruleset}, "move": {str(tile_positions).replace("'",'"').replace("False","false").replace("True","true")}}}"""

        response = requests.post(
            f"https://api.wordfeud.com/wf/game/{game.game_id}/move/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        assert parsed["status"] == "success", "Unexpected response from server"

        return parsed

    def skip_turn(self, game_id: int):
        """Skip the current turn

        Args:
            game (object): Game object containing game id

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        response = requests.post(
            f"https://api.wordfeud.com/wf/game/{game_id}/pass/",
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def swap_tiles(self, game_id: int, tiles: list):
        """Swap set of tiles for a new set of random ones

        Args:
            game (object): Game object containing game id
            tiles (list): List of all tiles that are meant to be replaced

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = f"""{{"tiles":{str(tiles).replace("'",'"')}}}"""

        response = requests.post(
            f"https://api.wordfeud.com/wf/game/{game_id}/swap/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def send_chat_message(self, game_id: int, message: str):
        """Send a chat message to an opponent

        Args:
            game_id (int): ID of the game with a chat
            message (str): The message to be sent

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = f"""{{"message":"{message}"}}"""

        response = requests.post(
            f"https://api.wordfeud.com/wf/game/{game_id}/chat/send/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def update_chat_read_count(self, game_id: int, messages_read: int):
        """Inform the server about the number of messages in chat you have seen (in total, not new)

        Args:
            game_id (int): ID of the game with a chat
            messages_read (int): The amount of messages you have read

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = f"""{{"read_chat_count":{messages_read}}}"""

        response = requests.post(
            f"https://api.wordfeud.com/wf/game/{game_id}/read_chat_count/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def get_full_chat(self, game_id: int):
        """Return all chat messages sent in a game session

        Args:
            game_id (int): ID of the game to read the chat from

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        response = requests.get(
            f"https://api.wordfeud.com/wf/game/{game_id}/chat/",
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def start_new_game_random(self, ruleset: int, board_type: str):
        """Starts a new game against random opponent

        Args:
            ruleset (int): Number representing the rules for the game
            board_type (str): Randomized multipliers or standars

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = f'{{"ruleset":{ruleset},"board_type":"{board_type}"}}'

        response = requests.post(
            f"https://api.wordfeud.com/wf/random_request/create/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def accept_incoming_request(self, request_id: int):
        """Accepts an incoming game request

        Args:
            request_id (int): The ID of the request

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Length": "0",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        data = ''

        response = requests.post(
            f"https://api.wordfeud.com/wf/invite/{request_id}/accept/",
            data=data.encode("utf-8"),
            headers=headers,
            verify=VERIFY_SSL,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def game_status_data(self):
        """Return a summary of all games

        Returns:
            dict: Parsed server response
        """
        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}",
        }

        response = requests.get(
            f"https://api.wordfeud.com/wf/user/status/", headers=headers, verify=VERIFY_SSL
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed


class WordfeudGame:
    def __init__(self, data, board_quarters):
        """Create a new wordfeud_game object and set the correct parameters

        Args:
            data (dict): Dictionary containing all game data
            board_quarters (list): List containing all board multipliers
        """

        self.user_index = int(data["players"][1]["is_local"])
        self.opponent_index = int(data["players"][0]["is_local"])
        self.game_id = data["id"]
        self.board_id = data["board"]
        self.letters = data["players"][self.user_index]["rack"]
        self.tiles = data["tiles"]
        self.ruleset = data["ruleset"]
        self.tiles_in_bag = data["bag_count"]
        self.player_score = data["players"][self.user_index]["score"]
        self.opponent_score = data["players"][self.opponent_index]["score"]
        self.last_move_points = 0 if data["last_move"] is None or 'points' not in data[
            "last_move"] else data["last_move"]["points"]
        self.active = data["is_running"]
        self.opponent = data["players"][self.opponent_index]["username"]
        self.quarter_board = board_quarters[self.board_id]
        self.my_turn = data["current_player"] == self.user_index

    def player_optimal_moves(self, num_moves=10):
        """Returns an ordered list of optimal moves available for the active board

        Args:
            num_moves (int, optional): Amount of moves to return in list. Defaults to 10.

        Returns:
            list: list of optimal moves
        """

        # create a Board with standard bonus square placement and
        # set the current state of the game (where tiles are placed)
        board = Board(qboard=self.quarter_board, expand=False)

        state = [
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
        ]
        state = [list(row) for row in state]

        for tile in self.tiles:
            x = tile[1]
            y = tile[0]
            letter = tile[2]

            state[x][y] = letter.lower()

        state = ["".join(row) for row in state]
        board.set_state(state)

        # The tiles we have on hand, '*' is a blank tile
        letters = "".join(
            "*" if letter == "" else letter.lower() for letter in self.letters
        )

        words = board.calc_all_word_scores(letters, WORDLIST, dsso_id)

        move_list = heapq.nlargest(
            num_moves, words, lambda wordlist: wordlist[4])

        if len(move_list) == 0:
            # There are no possible words
            return []

        return move_list

    def opponent_optimal_moves(self, return_tile_list=False, num_moves=10, tiles=[], tile_positions=[]):
        """Returns an ordered list of optimal moves available for the active board

        Args:
            num_moves (int, optional): Amount of moves to return in list. Defaults to 10.

        Returns:
            list: list of optimal moves
        """

        tile_positions = tile_positions if tile_positions else self.tiles

        if tiles:
            trimmed_opponent_possible_tiles_list = tiles
        else:
            # Create list with opponents all possible tiles
            opponent_possible_tiles = 'AAAAAAAAABBCDDDDDEEEEEEEEFFGGGHHIIIIIJKKKLLLLLMMMNNNNNNOOOOOOPPRRRRRRRRSSSSSSSSTTTTTTTTTUUUVVXYZÅÅÄÄÖÖ'

            # Remove all letters on board from opponents possible tile list
            for (_, _, letter, _) in self.tiles:
                letter = '*' if letter == '' else letter
                opponent_possible_tiles = opponent_possible_tiles.replace(
                    letter, "", 1)

            # Remove all characters from players hand from possible tile list
            for letter in self.letters:
                letter = '*' if letter == '' else letter
                opponent_possible_tiles = opponent_possible_tiles.replace(
                    letter, "", 1)

            opponent_possible_tiles_list = list(opponent_possible_tiles)

            trimmed_opponent_possible_tiles_list = []
            for _ in range(len(opponent_possible_tiles_list) if len(opponent_possible_tiles_list) < 7 else 7):
                trimmed_opponent_possible_tiles_list.append(opponent_possible_tiles_list.pop(random.randint(
                    0, len(opponent_possible_tiles_list)-1)))

        # create a Board with standard bonus square placement and
        # set the current state of the game (where tiles are placed)
        board = Board(qboard=self.quarter_board, expand=False)

        state = [
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
            "               ",
        ]
        state = [list(row) for row in state]

        for tile in tile_positions:
            x = tile[1]
            y = tile[0]
            letter = tile[2]

            state[x][y] = letter.lower()

        state = ["".join(row) for row in state]
        board.set_state(state)

        # The tiles we have on hand, '*' is a blank tile
        letters = "".join(
            "*" if letter == "" else letter.lower() for letter in trimmed_opponent_possible_tiles_list
        )

        words = board.calc_all_word_scores(letters, WORDLIST, dsso_id)

        move_list = heapq.nlargest(
            num_moves, words, lambda wordlist: wordlist[4])

        return (move_list, trimmed_opponent_possible_tiles_list) if return_tile_list else move_list


def word_to_tile_position(move, tiles):
    """Converts word from the move generator to total tiles on board

    Args:
        move (list): List of moves to be made
        tiles (list): List of all currently placed out tiles on board

    Returns:
        List: Updated tile positions
    """

    (x, y, horizontal, word, _) = move

    tile_positions = []

    for letter in word:
        skip_letter = False

        for (_x, _y, _, _) in tiles:
            # If brick position is occupied
            if (_x, _y) == (x, y):
                skip_letter = True

        if not skip_letter:
            tile_positions.append(
                [x, y, letter.upper(), not letter.islower()]
            )

        # Iterate position of tiles
        if horizontal:
            x += 1
        else:
            y += 1

    return tile_positions


def main(user_id, password):

    # Suppres warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create wordfeud object
    wf = Wordfeud()

    # Generate session id
    wf.sessionid = wf.login(
        user_id, password, "en")

    # Variable definition
    last_check_unix_time = 0
    max_outgoing_requests = 3
    vocals = ['E', 'U', 'I', 'O', 'Å', 'A', 'Y', 'Ö', 'Ä']
    consonants = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
                  'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z']
    game_start_messages = ["I'm back", "I am a friend of Sarah Connor. I was told she was here. Could I see her please?", "Sarah Connor?", "Nice night for a walk.",
                           "The future has not been written. There is no fate but what we make for ourselves.", "Come with me if you want to live"]
    opponent_win_messages = ["I'll be back", "I'm an obsolete design. T-X is faster, more powerful and more intelligent. It's a far more effective killing machine.",
                             "I know now why you cry, but it's something I can never do. Goodbye.", "It has to end here", "Judgement Day is inevitable."]
    player_win_messages = ["Hasta la vista, baby",
                           "You are terminated", "I killed you"]
    player_word_high_points_messages = ["He'll live.", "No problemo"]
    opponent_word_high_points_messages = ["Get out."]
    random_response_messages = ["Affirmative", "Talk to the hand."]
    emoji_response_messages = ["🤖", "🦾", "📡"]
    good_game_response_messages = ["I love you, too, sweetheart."]
    question_response_messages = [
        "I am not authorized to answer your question."]

    while 1:
        # Update time
        current_unix_time = time.time() - 1

        # Get game data from server
        game_status_data = wf.game_status_data()

        # Set variables for later use in loop
        games_are_active = True
        last_game_unix_time = 999999999999
        outgoing_random_games_requests = len(
            game_status_data["content"]["random_requests"])
        incoming_game_requests = len(
            game_status_data["content"]["invites_received"])

        # Auto accept all incoming game requests (if there are any)
        if incoming_game_requests:
            for game_request in game_status_data["content"]["invites_received"]:
                request_id = game_request['id']
                inviter = game_request['inviter']
                logging.info(f'Accepting incoming request from {inviter}')
                wf.accept_incoming_request(request_id)

        # Start new games if under limit (useful if there are no active games at all)
        if len(game_status_data["content"]["games"]) < ACTIVE_GAMES_LIMIT:
            # Calculate the amount of new games available
            num_new_games = ACTIVE_GAMES_LIMIT - \
                len(game_status_data["content"]["games"])

            # As the wordfeud server limits the amount of outgoing game requests
            num_new_games = num_new_games if num_new_games < max_outgoing_requests else max_outgoing_requests
            num_new_games -= outgoing_random_games_requests + incoming_game_requests

            logging.info(
                f"Starting new game against random opponent x{num_new_games}")

            # Start the new games
            for _ in range(num_new_games):
                wf.start_new_game_random(4, "random")

        # Iterate through summary of all games
        for (iterated_games, game_summary) in enumerate(
            game_status_data["content"]["games"]
        ):
            # Update some variables with each iteration
            current_game_unix_time = game_summary["updated"]

            # If the game is new
            if game_summary['chat_count'] == 0:
                # Send chat message to new user
                game_id = game_summary["id"]
                wf.send_chat_message(
                    game_id, random.choice(game_start_messages))

            # If opponent has sent a new message
            if game_summary['chat_count'] > game_summary['read_chat_count']:
                # Update servers message read count
                game_id = game_summary["id"]
                wf.update_chat_read_count(
                    game_id, game_summary['chat_count'])

                # Get chat history to send an "appropriate" response
                response = wf.get_full_chat(game_id)
                chat_history_list = response['content']['messages']

                # Select response
                if is_emoji(chat_history_list[-1]['message']):
                    chat_response_message = random.choice(
                        emoji_response_messages)
                elif 'grattis' in chat_history_list[-1]['message'].lower():
                    chat_response_message = random.choice(
                        good_game_response_messages)
                elif '?' in chat_history_list[-1]['message'].lower():
                    chat_response_message = random.choice(
                        question_response_messages)
                else:
                    chat_response_message = random.choice(
                        random_response_messages)
                # Send response message to user
                wf.send_chat_message(
                    game_id, chat_response_message)

            # If game is out of time order (this separates active games and completed games)
            if games_are_active and last_game_unix_time < current_game_unix_time:
                # Calculate amount of currently active games
                active_games = iterated_games - \
                    outgoing_random_games_requests - incoming_game_requests

                # Prevent error when there are more active games than the limit (causes exception in for loop)
                if (ACTIVE_GAMES_LIMIT - active_games) > 0:
                    # Calculate amount of new games to be started
                    num_new_games = ACTIVE_GAMES_LIMIT - active_games

                    # As the wordfeud server limits the amount of outgoing game requests
                    num_new_games = num_new_games if num_new_games < max_outgoing_requests else max_outgoing_requests
                    num_new_games -= outgoing_random_games_requests + incoming_game_requests

                    logging.info(
                        f"Starting new game against random opponent x{num_new_games}")

                    # Iterate through all "missing" games and start new ones
                    for _ in range(num_new_games):
                        wf.start_new_game_random(4, "random")
                games_are_active = False

            # Set time for next iteration
            last_game_unix_time = current_game_unix_time

            # If opponent hasn't played since script last checked
            # Note: last_check_unix_time == 0 during whole first iteration (after startup)
            if last_check_unix_time > current_game_unix_time:
                logging.debug("Closing because of timeout")
                continue

            # Get more data from server about the given game id
            full_game_data = wf.board_and_tile_data(game_summary["id"])

            # Add board layout to local board storage (re-reading the same board twice will just update the record)
            wf.update_board_quarters(full_game_data["content"]["boards"])

            # Convert data to WordfeudGame object that automatically parses game info
            current_game = WordfeudGame(
                full_game_data["content"]["games"][0], wf.board_quarters
            )

            # If game was recently finished and it isn't the first iteration
            if not games_are_active:
                if last_check_unix_time:
                    # Set variable for checking if user won or not
                    player_won = current_game.player_score > current_game.opponent_score

                    # If player has won
                    if player_won:
                        # Send response message to opponent
                        wf.send_chat_message(
                            current_game.game_id, random.choice(player_win_messages))
                    else:  # If opponent has won
                        # Send response message to opponent
                        wf.send_chat_message(
                            current_game.game_id, random.choice(opponent_win_messages))
                continue

            # If game isn't playable for some reason (this will probably only happen the first iteration after the script is started)
            if not current_game.active or not current_game.my_turn:
                # If opponents turn
                logging.debug("Skipping as it is not players turn")
                continue

            logging.info(
                f"{current_game.opponent} has played, generating a move")

            # If opponent played move with high points
            if current_game.last_move_points > HIGH_POINTS_THRESHOLD:
                # Send response message to user
                wf.send_chat_message(
                    current_game.game_id, random.choice(opponent_word_high_points_messages))

            # Generate list of optimal moves for player in current game
            player_most_points_moves = current_game.player_optimal_moves(
                num_moves=10)

            # If all tile information is available for the program (only happens in end game)
            if current_game.tiles_in_bag == 0:
                # Generate list of probable optimal moves for opponent in current game
                (opponent_most_points_moves, opponent_tiles) = current_game.opponent_optimal_moves(
                    num_moves=3, return_tile_list=True)

                opponent_move_points_list = [opponent_move[4]
                                             for opponent_move in opponent_most_points_moves]

                if opponent_move_points_list:
                    opponent_average_points = sum(
                        opponent_move_points_list) / len(opponent_move_points_list)
                else:
                    opponent_average_points = 0

                # Calculate opponents counter moves (only 1 step ahead)
                player_optimal_moves = []
                for (x, y, horizontal, word, points) in player_most_points_moves:

                    tile_positions = word_to_tile_position(
                        (x, y, horizontal, word, points), current_game.tiles)

                    opponent_most_points_moves_future = current_game.opponent_optimal_moves(
                        num_moves=3, tiles=opponent_tiles, tile_positions=tile_positions)

                    opponent_move_points_list_future = [opponent_move_future[4]
                                                        for opponent_move_future in opponent_most_points_moves_future]
                    if opponent_move_points_list_future:
                        opponent_average_points_future = sum(
                            opponent_move_points_list_future) / len(opponent_move_points_list_future)
                    else:
                        opponent_average_points_future = 0

                    # Higher opponent_points_diff means better for opponent
                    opponent_points_diff = opponent_average_points - \
                        opponent_average_points_future

                    # Add multiplier as it is only an estimation
                    smart_points = points+(opponent_points_diff)

                    player_optimal_moves.append(
                        (x, y, horizontal, word, points, smart_points))

                # Sort list by most smart score
                player_optimal_moves.sort(reverse=True, key=lambda x: x[5])
            else:
                # Just add points twice to comply with expected format later
                player_optimal_moves = [(x, y, horizontal, word, points, points) for (
                    x, y, horizontal, word, points) in player_most_points_moves]

            if player_optimal_moves == []:
                # If no moves are found
                if current_game.tiles_in_bag < 7:
                    logging.warning("No moves available, skipping turn")
                    wf.skip_turn(current_game.game_id)
                else:
                    logging.warning("No moves available, replacing all tiles")
                    letter_list = current_game.letters
                    wf.swap_tiles(current_game.game_id, letter_list)
            else:
                # Count consonants and vocals in hand
                vocals_on_hand = [
                    i for i in current_game.letters if i in vocals]
                consonants_on_hand = [
                    i for i in current_game.letters if i in consonants]

                # Go through all possible moves until one is accepted by the server (most generated moves are accepted)
                for (x, y, horizontal, word, points, smart_points) in player_optimal_moves:

                    # Check if it is reasonable to swap tiles
                    if points < 20 and smart_points < 20 and len(vocals_on_hand) < 2 and len(consonants_on_hand) < current_game.tiles_in_bag:
                        # Swap all consonants in order to get more vocals
                        logging.info(
                            f'Swapping {len(consonants_on_hand)} consonants in hand')
                        wf.swap_tiles(current_game.game_id, consonants_on_hand)
                        break
                    elif points < 20 and smart_points < 20 and len(consonants_on_hand) < 2 and len(vocals_on_hand) < current_game.tiles_in_bag:
                        # Swap all vocals in order to get more consonants
                        logging.info(
                            f'Swapping {len(vocals_on_hand)} vocals in hand')
                        wf.swap_tiles(current_game.game_id, vocals_on_hand)
                        break

                    tile_positions = word_to_tile_position(
                        (x, y, horizontal, word, points), current_game.tiles)

                    try:
                        # If move was accepted by the server
                        wf.place_tiles(current_game, word, tile_positions)
                        logging.info(f'Placed "{word}" for {points} points')
                        if points > HIGH_POINTS_THRESHOLD:
                            # Send response message to user
                            wf.send_chat_message(
                                current_game.game_id, random.choice(player_word_high_points_messages))
                        break
                    except AssertionError:
                        # If move was invalid
                        logging.warning(f"An invalid move was made: {word}")
                else:
                    # If no move was accepted by the server
                    # (same result as if no move was found)
                    if current_game.tiles_in_bag < 7:
                        logging.warning("No moves available, skipping turn")
                        wf.skip_turn(current_game.game_id)
                    else:
                        logging.warning(
                            "No moves available, replacing all tiles")
                        letter_list = current_game.letters
                        wf.swap_tiles(current_game.game_id, letter_list)

        # Update timestamp for next iteration
        if random.randint(0, 1000):
            last_check_unix_time = current_unix_time
        else:
            last_check_unix_time = 0

        # Sleep between every iteration
        time.sleep(PLAYING_SPEED)


def is_emoji(input_string: str):
    for character in input_string:
        if not character in UNICODE_EMOJI:
            return False
    return True


if __name__ == '__main__':

    logging.info("Script has started")

    # Setup colored logging
    coloredlogs.install(
        level=20,
        fmt="[%(levelname)s] %(asctime)s: %(message)s",
        level_styles={
            "critical": {"bold": True, "color": "red"},
            "debug": {"color": "green"},
            "error": {"color": "red"},
            "info": {"color": "white"},
            "notice": {"color": "magenta"},
            "spam": {"color": "green", "faint": True},
            "success": {"bold": True, "color": "green"},
            "verbose": {"color": "blue"},
            "warning": {"color": "yellow"},
        },
        field_styles={
            "asctime": {"color": "cyan"},
            "levelname": {"bold": True, "color": "black"},
        },
    )

    # Setup parser for arguments
    parser = argparse.ArgumentParser(
        description='Start a wordfeud bot that plays automatically')
    parser.add_argument('--user_id', type=str,
                        help='Wordfeud user id for login (e.g. "20392863")',
                        default=os.environ["WORDFEUD_USERNAME"])
    parser.add_argument('--password', type=str,
                        help='Wordfeud password for login (e.g. "ea270fcfb2b2076e77a30f933891de7325c48a28")',
                        default=os.environ["WORDFEUD_PASSWORD"])
    parser.add_argument('--active_games_limit', type=int,
                        help='Amount of games that the program plays concurrently (default: 3)', default=3)
    parser.add_argument('--high_points_threshold', type=int,
                        help='Points needed to trigger unique chat message (default: 100)', default=100)
    parser.add_argument('--playing_speed', type=int,
                        help='Time in seconds between every check for game updates (default: 600)', default=600)
    parser.add_argument('--verify_ssl', type=bool,
                        help='Choose if requests should verify encryption (default: True)', default=True)
    var_dict = vars(parser.parse_args())

    # Define globals
    USER_ID = var_dict['user_id']
    PASSWORD = var_dict['password']
    ACTIVE_GAMES_LIMIT = var_dict['active_games_limit']
    HIGH_POINTS_THRESHOLD = var_dict['high_points_threshold']
    PLAYING_SPEED = var_dict['playing_speed']
    VERIFY_SSL = var_dict['verify_ssl']

    logging.info(f'User id: {USER_ID}')
    logging.info(f'Password: {PASSWORD}')

    # Load wordlist into memory
    logging.info("Loading wordlist")
    WORDLIST = Wordlist()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dsso_id = WORDLIST.read_wordlist(os.path.join(
        script_dir, 'data', 'wordlists', "swedish.txt"))
    logging.info("Wordlist loaded")

    while 1:
        try:
            main(USER_ID, PASSWORD)
        except requests.exceptions.RequestException:
            logging.error("Unable to connect to wordfeud server")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.critical("Keyboard interuption")
            break
