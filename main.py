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

    def board_and_tile_data(self):
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

        response = requests.get(
            'https://api.wordfeud.com/wf/user/games/detail/?known_tile_points=&known_boards=', headers=headers, verify=False)

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

        assert (parsed['status'] ==
                'success'), 'Unexpected response from server'

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

        print(tiles)

        data = f'''{{"tiles":{urllib.parse.quote(str(tiles).replace("'",'"'))}}}'''

        response = requests.post(
            f'https://api.wordfeud.com/wf/game/{game.id}/swap/', data=data, headers=headers, verify=False)

        parsed = response.json()

        assert (parsed['status'] ==
                'success'), 'Unexpected response from server'

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

        assert (parsed['status'] ==
                'success'), 'Unexpected response from server'

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

tiles_and_game_data = wf.board_and_tile_data()

games = []
time_since_last_play = time.time()

while 1:
    # Sleep between every iteration
    time.sleep(120)

    tiles_and_game_data = wf.board_and_tile_data()

    if (len(tiles_and_game_data['content']['games'])-len(games)) > 0:
        # If wordfeud server has more records of games than client has
        wf.update_board_quarters(tiles_and_game_data['content']['boards'])

        for game_data in tiles_and_game_data['content']['games']:
            for game in games:
                if game.id == game_data['id']:
                    break
            else:
                # If game data id was not found in local copy, append it to local copy
                games.append(WordfeudGame(game_data, wf.board_quarters))

        # for i in range(len(tiles_and_game_data['content']['games'])-len(games), 0, -1):
        #     # Add new game to game list
        #     games.append(WordfeudGame(tiles_and_game_data['content']
        #                               ['games'][-i], wf.board_quarters))

    game_data = tiles_and_game_data['content']['games']

    for game in games:

        # Iterate through all game data in order to match local and server game data
        for game_data in tiles_and_game_data['content']['games']:
            if game.id == game_data['id']:
                break
        else:
            # Game has been completed and removed, so local version is removed too
            games.remove(game)
            continue

        game.update(game_data)

        if game.active and game.my_turn:
            time_since_last_play = time.time()
            logging.info(f'{game.opponent} has played, generating a move')
            optimal_moves = game.optimal_moves()

            if optimal_moves == []:
                if game.tiles_in_bag < 7:
                    logging.warning('No moves available, skipping turn')
                    wf.skip_turn(game)
                else:
                    logging.warning('No moves available, replacing all tiles')
                    letter_list = game.letters
                    # wf.swap_tiles(game, letter_list)
                    wf.skip_turn(game)
            else:
                for (x, y, horizontal, word, points) in optimal_moves:
                    tile_positions = []

                    for letter in word:
                        skip_letter = False

                        for (_x, _y, _, _) in game.tiles:
                            # If brick position is occupied
                            if (_x, _y) == (x, y):
                                skip_letter = True

                        if not skip_letter:
                            tile_positions.append(
                                [x, y, letter.upper(), not letter.islower()])

                        # Iterate position of bricks
                        if horizontal:
                            x += 1
                        else:
                            y += 1

                    try:
                        wf.place_tiles(game, word, tile_positions)
                        logging.info(f'Placed {word} for {points} points')
                        break
                    except AssertionError:
                        # If move was invalid
                        logging.warning('An invalid move was made')
                        continue
