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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup colored logging
coloredlogs.install(level=20, fmt="[%(levelname)s] %(asctime)s: %(message)s", level_styles={'critical': {'bold': True, 'color': 'red'}, 'debug': {'color': 'green'}, 'error': {'color': 'red'}, 'info': {
                    'color': 'white'}, 'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True}, 'success': {'bold': True, 'color': 'green'}, 'verbose': {'color': 'blue'}, 'warning': {'color': 'yellow'}}, field_styles={'asctime': {'color': 'cyan'}, 'levelname': {'bold': True, 'color': 'black'}})

logging.info('Script has started')


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
            "Accept-Encoding": "gzip"
        }

        data = f'{{"id": {user_id}, "password": "{password}", "language_code": "{language_code}"}}'

        response = requests.post('https://api.wordfeud.com/wf/user/login/id/', headers=headers,
                                 data=data, verify=False)

        # Verify that server accepted credentials
        if response.json()['status'] == 'error':
            raise Exception('Server returned error message')

        # Make cookies into a dictionary
        cookies = response.cookies.get_dict()

        # Return sessionid
        sessionid = cookies['sessionid']
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
            "Cookie": f"sessionid={self.sessionid}"
        }

        if game_id is None:
            # Data about all games
            response = requests.get(
                f'https://api.wordfeud.com/wf/user/games/detail/?known_tile_points=&known_boards=', headers=headers, verify=False)
        else:
            # Data about specific game
            response = requests.get(
                f'https://api.wordfeud.com/wf/games/{game_id}/?known_tile_points=&known_boards=', headers=headers, verify=False)

        parsed = response.json()
        return parsed

    def update_board_quarters(self, board_list):
        self.board_quarters = {}
        multiplier_number_to_text_dict = {
            0: '--', 1: '2l', 2: '3l', 3: '2w', 4: '3w'}

        default_board_placements = ['-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --',
                                    '-- -- -- -- -- -- -- -- -- -- -- -- -- -- --']
        for board in board_list:
            board_id = board['board_id']

            board_placements = default_board_placements
            board_placements = [row.split(' ') for row in board_placements]

            for row in range(len(board['board'])):
                for column in range(len(board['board'][row])):
                    multiplier_value_int = board['board'][row][column]
                    board_placements[row][column] = multiplier_number_to_text_dict[multiplier_value_int]

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
            'Content-Length': '0',
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}"
        }

        data = f'''{{"words": ["{word.upper()}"], "ruleset": {game.ruleset}, "move": {str(tile_positions).replace("'",'"').replace("False","false").replace("True","true")}}}'''

        response = requests.post(
            f'https://api.wordfeud.com/wf/game/{game.id}/move/', data=data, headers=headers, verify=False)

        parsed = response.json()

        assert (parsed['status'] ==
                'success'), 'Unexpected response from server'

        return parsed

    def skip_turn(self, game):
        """Skip the current turn

        Args:
            game (object): Game object containing game id

        Returns:
            dict: Parsed server response
        """

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            'Content-Length': '0',
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}"
        }

        response = requests.post(
            f'https://api.wordfeud.com/wf/game/{game.id}/pass/', headers=headers, verify=False)

        parsed = response.json()

        if not (parsed['status'] == 'success'):
            logging.error(
                f'Unexpected response from server in {inspect.stack()[0][3]}')

        return parsed

    def swap_tiles(self, game: object, tiles: list):
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
            'Content-Length': '0',
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}"
        }

        data = f'''{{"tiles":{urllib.parse.quote(str(tiles).replace("'",'"'))}}}'''

        response = requests.post(
            f'https://api.wordfeud.com/wf/game/{game.id}/swap/', data=data, headers=headers, verify=False)

        parsed = response.json()

        if not (parsed['status'] == 'success'):
            logging.error(
                f'Unexpected response from server in {inspect.stack()[0][3]}')

        return parsed

    def start_new_game_random(self, ruleset: int, board_type: str):

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            'Content-Length': '0',
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}"
        }

        data = f'{{"ruleset":{ruleset},"board_type":"{board_type}"}}'

        response = requests.post(
            f'https://api.wordfeud.com/wf/random_request/create/', data=data, headers=headers, verify=False)

        parsed = response.json()

        if not (parsed['status'] == 'success'):
            logging.error(
                f'Unexpected response from server in {inspect.stack()[0][3]}')

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
            "Cookie": f"sessionid={self.sessionid}"
        }

        response = requests.get(
            f'https://api.wordfeud.com/wf/user/status/', headers=headers, verify=False)

        parsed = response.json()

        if not (parsed['status'] == 'success'):
            logging.error(
                f'Unexpected response from server in {inspect.stack()[0][3]}')

        return parsed


class WordfeudGame:
    def __init__(self, data, board_quarters):
        """Create a new wordfeud_game object and set the correct parameters

        Args:
            data (dict): Dictionary containing all game data
            board_quarters (list): List containing all board multipliers
        """

        self.user_id = int(data['players'][1]['is_local'])
        self.opponent_id = int(data['players'][0]['is_local'])
        self.id = data['id']
        self.board_id = data['board']
        self.letters = data['players'][self.user_id]['rack']
        self.tiles = data['tiles']
        self.ruleset = data['ruleset']
        self.tiles_in_bag = data['bag_count']
        self.active = data['is_running']
        self.opponent = data['players'][self.opponent_id]['username']
        self.quarter_board = board_quarters[self.board_id]
        self.my_turn = data['current_player'] == self.user_id

    def update(self, data):
        """Updates game data with new information

        Args:
            data (dict): Dictionary containing all game data
        """

        self.letters = data['players'][self.user_id]['rack']
        self.tiles = data['tiles']
        self.active = data['is_running']
        self.tiles_in_bag = data['bag_count']
        self.my_turn = data['current_player'] == self.user_id

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

        state = ['               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ',
                 '               ']
        state = [list(row) for row in state]

        for tile in self.tiles:
            x = tile[1]
            y = tile[0]
            letter = tile[2]

            state[x][y] = letter.lower()

        state = [''.join(row) for row in state]
        board.set_state(state)

        # The tiles we have on hand, '*' is a blank tile
        letters = ''.join('*' if letter == '' else letter.lower()
                          for letter in self.letters)

        words = board.calc_all_word_scores(letters, wordlist, dsso_id)

        move_list = heapq.nlargest(
            num_moves, words, lambda wordlist: wordlist[4])

        if len(move_list) == 0:
            # There are no possible words
            return []

        return move_list


# Create wordfeud object
wf = Wordfeud()

# Load wordlist into memory
logging.info('Loading wordlist')
wordlist = Wordlist()
dsso_id = wordlist.read_wordlist(os.path.join('wordlists', 'swedish.txt'))

# Generate session id
wf.sessionid = wf.login(
    32947023, 'ea277fcfa2b2076f47430f913891dc8523c28e67', 'en')

# Define variables
last_check_unix_time = 0
games = []

while 1:
    # Sleep between every iteration
    time.sleep(120)

    # Temporary solution for starting new games
    wf.start_new_game_random(4, 'random')

    current_unix_time = time.time()
    game_status_data = wf.game_status_data()

    # Iterate through summary of all games
    for game_summary in game_status_data['content']['games']:

        # If opponent hasn't played since script last checked
        if last_check_unix_time > game_summary['updated']:
            logging.debug('Closing because of timeout')
            break  # Stop iteration of game summaries, as they are all sorted by time and the following elements therefore won't pass this check either

        # Get more data from server about the given game id
        full_game_data = wf.board_and_tile_data(game_summary['id'])

        # Add board layout to local board storage (re-reading the same board twice will just update the record)
        wf.update_board_quarters(full_game_data['content']['boards'])

        # Convert data to WordfeudGame object that automatically parses game info
        current_game = WordfeudGame(
            full_game_data['content']['games'][0], wf.board_quarters)

        # If game isn't playable for some reason (this will probably only happen the first iteration after the script is started)
        if not current_game.active:
            # If game has ended
            if last_check_unix_time:
                # Only start new game if this isn't the first iteration
                logging.debug('Game has ended, starting a new one')
                wf.start_new_game_random(4, 'random')
            continue
        elif not current_game.my_turn:
            # If opponents turn
            logging.debug('Skipping as it is not players turn')
            continue

        logging.info(f'{current_game.opponent} has played, generating a move')

        # Generate list of optimal moves for current game
        optimal_moves = current_game.optimal_moves(num_moves=10)

        if optimal_moves == []:
            # If no moves are found
            if current_game.tiles_in_bag < 7:
                logging.warning('No moves available, skipping turn')
                wf.skip_turn(current_game)
            else:
                logging.warning('No moves available, replacing all tiles')
                letter_list = current_game.letters
                # wf.swap_tiles(game, letter_list)
                wf.skip_turn(current_game)
        else:
            # Go through all possible moves until one is accepted by the server (most generated moves are accepted)
            for (x, y, horizontal, word, points) in optimal_moves:
                tile_positions = []

                for letter in word:
                    skip_letter = False

                    for (_x, _y, _, _) in current_game.tiles:
                        # If brick position is occupied
                        if (_x, _y) == (x, y):
                            skip_letter = True

                    if not skip_letter:
                        tile_positions.append(
                            [x, y, letter.upper(), not letter.islower()])

                    # Iterate position of tiles
                    if horizontal:
                        x += 1
                    else:
                        y += 1

                try:
                    # If move was accepted by the server
                    wf.place_tiles(current_game, word, tile_positions)
                    logging.info(f'Placed "{word}" for {points} points')
                    break
                except AssertionError:
                    # If move was invalid
                    logging.warning('An invalid move was made')
            else:
                # If no move was accepted by the server
                # (same result as if no move was found)
                if current_game.tiles_in_bag < 7:
                    logging.warning('No moves available, skipping turn')
                    wf.skip_turn(current_game)
                else:
                    logging.warning('No moves available, replacing all tiles')
                    letter_list = current_game.letters
                    # wf.swap_tiles(game, letter_list)
                    wf.skip_turn(current_game)
                pass

    # Update timestamp for next iteration
    last_check_unix_time = current_unix_time
