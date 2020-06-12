#!/usr/bin/python3
# -*- coding: utf-8 -*-

from emoji import UNICODE_EMOJI
import requests
from wordfeud_logic.wordlist import Wordlist
from wordfeud_logic.board import Board
import heapq
import time
import urllib3
import urllib
import coloredlogs
import logging
import os
import inspect
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

logging.info("Script has started")


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
            verify=False,
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
                verify=False,
            )
        else:
            # Data about specific game
            response = requests.get(
                f"https://api.wordfeud.com/wf/games/{game_id}/?known_tile_points=&known_boards=",
                headers=headers,
                verify=False,
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
            verify=False,
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
            verify=False,
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
            verify=False,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def send_chat_message(self, game_id: int, message: str):

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
            verify=False,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def update_chat_read_count(self, game_id: int, messages_read: int):

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
            verify=False,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def get_full_chat(self, game_id: int):

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
            verify=False,
        )

        parsed = response.json()

        if not (parsed["status"] == "success"):
            logging.error(
                f"Unexpected response from server in {inspect.stack()[0][3]}")

        return parsed

    def start_new_game_random(self, ruleset: int, board_type: str):

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
            verify=False,
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
            f"https://api.wordfeud.com/wf/user/status/", headers=headers, verify=False
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
        self.score_position = data["players"][self.user_index]["position"]
        self.last_move_points = 0 if data["last_move"] == None or 'points' not in data[
            "last_move"] else data["last_move"]["points"]
        self.active = data["is_running"]
        self.opponent = data["players"][self.opponent_index]["username"]
        self.quarter_board = board_quarters[self.board_id]
        self.my_turn = data["current_player"] == self.user_index

    def update(self, data):
        """Updates game data with new information

        Args:
            data (dict): Dictionary containing all game data
        """

        self.letters = data["players"][self.user_index]["rack"]
        self.tiles = data["tiles"]
        self.active = data["is_running"]
        self.tiles_in_bag = data["bag_count"]
        self.my_turn = data["current_player"] == self.user_index

    def optimal_moves(self, num_moves=10):
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

        words = board.calc_all_word_scores(letters, wordlist, dsso_id)

        move_list = heapq.nlargest(
            num_moves, words, lambda wordlist: wordlist[4])

        if len(move_list) == 0:
            # There are no possible words
            return []

        return move_list


def main(user_id, password):
    # Create wordfeud object
    wf = Wordfeud()

    # Generate session id
    wf.sessionid = wf.login(
        user_id, password, "en")

    # Variable definition
    last_check_unix_time = 0
    games = []
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
    opponent_word_high_points_messages = ["Fuck you asshole.", "Get out."]
    random_response_messages = [
        "I am not authorized to answer your question.", "Affirmative", "Talk to the hand."]
    emoji_response_messages = ["🤖", "🦾", "📡"]

    while 1:
        # Sleep between every iteration
        time.sleep(PLAYING_SPEED)

        # Get game data from server
        game_status_data = wf.game_status_data()

        games_are_active = True
        current_unix_time = time.time()
        last_game_unix_time = 999999999999
        outgoing_random_games_requests = len(
            game_status_data["content"]["random_requests"])

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
                    chat_response_message = "I love you, too, sweetheart."
                else:
                    chat_response_message = random.choice(
                        random_response_messages)
                # Send response message to user
                wf.send_chat_message(
                    game_id, random.choice(chat_response_message))

            # If game is out of time order (this separates active games and completed games)
            if games_are_active and last_game_unix_time < current_game_unix_time:
                # Calculate amount of currently active games
                active_games = iterated_games - outgoing_random_games_requests

                # Prevent error when there are more active games than the limit (causes exception in for loop)
                if (ACTIVE_GAMES_LIMIT - active_games) > 0:
                    logging.info("Starting new game against random opponent")
                    # Iterate through all "missing" games and start new ones
                    for _ in range(ACTIVE_GAMES_LIMIT - active_games):
                        wf.start_new_game_random(4, "random")
                games_are_active = False

            # Set time for next iteration
            last_game_unix_time = current_game_unix_time

            # If opponent hasn't played since script last checked
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

            # If game was recently finished
            if not games_are_active:
                player_position = current_game.score_position

                # If player has won
                if player_position == 0:
                    # Send response message to user
                    wf.send_chat_message(
                        current_game.game_id, random.choice(player_win_messages))
                else:  # If opponent has won
                    # Send response message to user
                    wf.send_chat_message(
                        current_game.game_id, random.choice(opponent_win_messages))
                continue

            # If game isn't playable for some reason (this will probably only happen the first iteration after the script is started)
            if not current_game.active:
                # If game has ended
                if last_check_unix_time:
                    # Only start new game if this isn't the first iteration
                    logging.debug("Game has ended, starting a new one")
                    wf.start_new_game_random(4, "random")
                continue
            elif not current_game.my_turn:
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

            # Generate list of optimal moves for current game
            optimal_moves = current_game.optimal_moves(num_moves=10)

            if optimal_moves == []:
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
                for (x, y, horizontal, word, points) in optimal_moves:

                    # Check if it is reasonable to swap tiles
                    if points < 20 and len(vocals_on_hand) < 2 and len(consonants_on_hand) < current_game.tiles_in_bag:
                        # Swap all consonants in order to get more vocals
                        logging.info('Swapping all consonants in hand')
                        wf.swap_tiles(current_game.game_id, consonants_on_hand)
                        break
                    elif points < 20 and len(consonants_on_hand) < 2 and len(vocals_on_hand) < current_game.tiles_in_bag:
                        # Swap all vocals in order to get more consonants
                        logging.info('Swapping all vocals in hand')
                        wf.swap_tiles(current_game.game_id, vocals_on_hand)
                        break

                    tile_positions = []

                    for letter in word:
                        skip_letter = False

                        for (_x, _y, _, _) in current_game.tiles:
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
                    pass

        # Update timestamp for next iteration
        last_check_unix_time = current_unix_time


def is_emoji(s: str):
    return s in UNICODE_EMOJI


if __name__ == '__main__':

    # Load wordlist into memory
    logging.info("Loading wordlist")
    wordlist = Wordlist()
    dsso_id = wordlist.read_wordlist(os.path.join("wordlists", "swedish.txt"))
    logging.info("Wordlist loaded")

    ### User defined variables ###
    ACTIVE_GAMES_LIMIT = 30  # Amount of games that the program plays concurrently
    HIGH_POINTS_THRESHOLD = 100  # Points needed to trigger unique chat message
    PLAYING_SPEED = 60  # Time in seconds between every check for game updates
    USER_ID = 32947023  # Account user id to log in with
    PASSWORD = 'ea277fcfa2b2076f47430f913891dc8523c28e67'   # Account password

    while 1:
        try:
            main(USER_ID, PASSWORD)
        except requests.exceptions.RequestException:
            logging.error("Unable to connect to wordfeud server")
        except KeyboardInterrupt:
            logging.critical("Keyboard interuption")
            break
