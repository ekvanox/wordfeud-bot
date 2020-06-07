import requests
from wordfeudplayer.wordlist import Wordlist
from wordfeudplayer.board import Board
import heapq
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class wordfeud:
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

        headers = {
            "User-Agent": "WebFeudClient/3.0.17 (Android 10)",
            "Content-Type": "application/json; charset=UTF-8",
            'Content-Length': '0',
            "Host": "api.wordfeud.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": f"sessionid={self.sessionid}"
        }

        data = f'''{{"words": ["{word.upper()}"], "ruleset": {game.ruleset}, "move": {str(tile_positions).replace("'",'"').replace("False","false")}}}'''

        response = requests.post(
            f'https://api.wordfeud.com/wf/game/{game.id}/move/', data=data, headers=headers, verify=False)

        parsed = response.json()

        assert (parsed['status'] ==
                'success'), 'Unexpected response from server'

        return parsed


class wordfeud_game:
    def __init__(self, data, board_quarters):
        self.id = data['id']
        self.board_id = data['board']
        self.letters = data['players'][0]['rack']
        self.tiles = data['tiles']
        self.ruleset = data['ruleset']
        self.quarter_board = board_quarters[self.board_id]
        self.my_turn = data['current_player'] == 0

    def update(self, data):
        self.letters = data['players'][0]['rack']
        self.tiles = data['tiles']
        self.my_turn = data['current_player'] == 0

    def optimal_moves(self, num_moves=10):
        # create a Wordlist and tell it to read one or more wordlists
        wordlist = Wordlist()
        dsso_id = wordlist.read_wordlist('ordlista.txt')

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

        # the letters we have on hand, '*' is a blank tile
        letters = ''.join(letter.lower() for letter in self.letters)

        # Make the wildcard tile usable
        letters.replace('', '*')

        # calculate all possible words and their scores
        top20 = calc_best_moves(board, wordlist, letters, dsso_id)
        return top20


def calc_best_moves(b, w, letters, variant, num_moves=20):
    words = b.calc_all_word_scores(letters, w, variant)

    # pick out the 20 words with highest score and print them
    top20 = heapq.nlargest(num_moves, words, lambda w: w[4])

    if len(top20) == 0:
        # There are no possible words
        return []

    # print('Score StartX StartY  Direction Word (capital letter means "use wildcard")')
    # for (x, y, horizontal, word, score) in top20:
    #     print('%5d %6d %6s %10s %s' %
    #           (score, x, y, 'Horizontal' if horizontal else 'Vertical', word))

    return top20


# Create wordfeud object
wf = wordfeud()

# Generate session id
wf.sessionid = wf.login(
    32947023, 'ea277fcfa2b2076f47430f913891dc8523c28e67', 'en')

tiles_and_game_data = wf.board_and_tile_data()

wf.update_board_quarters(tiles_and_game_data['content']['boards'])

game = wordfeud_game(tiles_and_game_data['content']
                     ['games'][0], wf.board_quarters)

while 1:
    time.sleep(1)

    tiles_and_game_data = wf.board_and_tile_data()

    game.update(tiles_and_game_data['content']['games'][0])

    if game.my_turn:
        print('Opponent has played, generating a move')
        optimal_moves = game.optimal_moves()

        for (x, y, horizontal, word, points) in optimal_moves:
            tile_positions = []

            for letter in word:
                skip_letter = False

                for (_x, _y, _, _) in game.tiles:
                    # If brick position is occupied
                    if (_x, _y) == (x, y):
                        skip_letter = True

                if not skip_letter:
                    tile_positions.append([x, y, letter.upper(), False])

                if horizontal:
                    x += 1
                else:
                    y += 1

            try:
                wf.place_tiles(game, word, tile_positions)
                print('Done')
                break
            except AssertionError:
                continue
