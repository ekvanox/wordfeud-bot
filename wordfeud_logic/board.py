# -*- coding: utf-8 -*-

# (c) 2011, Marcus Svensson <macke77@gmail.com>
# See gpl-2.0.txt for license


_default_quarter_board = ['3l -- -- -- 3w -- -- 2l',
                          '-- 2l -- -- -- 3l -- --',
                          '-- -- 2w -- -- -- 2l --',
                          '-- -- -- 3l -- -- -- 2w',
                          '3w -- -- -- 2w -- 2l --',
                          '-- 3l -- -- -- 3l -- --',
                          '-- -- 2l -- 2l -- -- --',
                          '2l -- -- 2w -- -- -- ss']

_letter_points = {'a': 1,
                  'b': 3,
                  'c': 8,
                  'd': 1,
                  'e': 1,
                  'f': 3,
                  'g': 2,
                  'h': 3,
                  'i': 1,
                  'j': 7,
                  'k': 3,
                  'l': 2,
                  'm': 3,
                  'n': 1,
                  'o': 2,
                  'p': 4,
                  'r': 1,
                  's': 1,
                  't': 1,
                  'u': 4,
                  'v': 3,
                  'x': 8,
                  'y': 7,
                  'z': 8,
                  'å': 4,
                  'ä': 4,
                  'ö': 4}


class Board(object):

    def __init__(self, qboard=_default_quarter_board, expand=True):
        '''Initializes a playing board that keeps track of where
        the bonus squares are.
        :param qboard  A board represented by a list of strings
                       (see _default_quarter_board for an example)
        :param expand  If true qboard will be interpreted as the
                       upper left quarter of a four times larger
                       board (good for symetrical layouts)'''
        self.board = self.expand_quarter_board(qboard) if expand else qboard
        N = len(self.board)
        self.empty_row = ' '*N
        self.horizontal = [self.empty_row]*N
        self.vertical = [self.empty_row]*N

    # make hashable
    def __hash__(self):
        return self.horizontal.__hash__()

    def __eq__(self, other):
        try:
            return self.horizontal.__eq__(other.horizontal)
        except:
            return False

    @classmethod
    def expand_quarter_board(cls, qb):
        '''Takes a quarter board and expands it to a whole board by mirroring it in
        the four possible ways'''
        qbs = [r.split(' ') for r in qb]
        b = [0] * (len(qbs)*2-1)
        for i, row in enumerate(qbs):
            b[i] = b[-i-1] = row + row[-2::-1]
        return b

    def set_state(self, rows):
        '''Sets the current state of the board, ie which letter is on what position
        :param rows a list of strings - one for each row'''
        self.horizontal = rows[:]
        self.vertical = [''.join(r) for r in zip(*rows)]

    def is_occupied(self, x, y):
        try:
            return self.vertical[x][y] != ' '
        except:
            return False

    def play_word(self, word, x, y, horizontal):
        '''Modifies the board by writing a word to it
        :param x The x coordinate that the word starts at
        :param y The y coordinate that the word starts at
        :param horizontal True if the word is horizontal, False if it is vertical'''
        (dx, dy) = (1,0) if horizontal else (0,1)
        for ch in word.lower():
            self.horizontal[y] = self.horizontal[y][:x] + ch + self.horizontal[y][x+1:]
            x += dx
            y += dy
        self.set_state(self.horizontal)

    @classmethod
    def start_end(cls, row, i):
        '''Returns the beginning and end of the word at position i given that a character would be placed in i
        :param row The row as a string with spaces for unfilled positions
        :i The position for which we want to know the surrounding word'''
        start = row.rfind(' ', 0, i)+1
        end = row.find(' ', i+1)
        if end == -1:
            end = len(row)
        assert(start<end)
        return (start, end)

    def surrounding_words(self, horizontal, i):
        '''Returns the surrounding characters that would need to form a valid word
        in order to fill each position in the i'th row of the board'''
        crossing_rows = self.vertical if horizontal else self.horizontal
        for row in crossing_rows:
            (start, end) = self.start_end(row, i)
            yield row[start:end].lower()

    def calc_word_points(self, word, x0, y0, horizontal, include_crossing_words=True):
        '''Calculates the score of a word that has not yet been played to the board
        :param word The word
        :param x0 The x coordinate where the first letter of the word will be played (or already is)
        :param y0 The y coordinate where the first letter of the word will be played (or already is)
        :param horizontal True if is a horizontal word, False if vertical
        :param include_crossing_words True if the points for crossing words should be included too'''
        word_multiplicator = 1
        word_points = 0
        tiles_used = 0
        total_points = 0
        (x, y) = (x0, y0)
        (dx, dy) = (1,0) if horizontal else (0,1)
        for i, ch in enumerate(word):
            letter_points = _letter_points.get(ch, 0)
            if self.horizontal[y][x] == ' ':
                tiles_used += 1
                square_bonus = self.board[y][x]
                if square_bonus[1] == 'l':
                    letter_points *= int(square_bonus[0])
                elif square_bonus[1] == 'w':
                    word_multiplicator *= int(square_bonus[0])

                if include_crossing_words:
                    crow, ci = (self.vertical[x], y) if horizontal else (self.horizontal[y], x)
                    s, e = self.start_end(crow, ci)
                    if e-s > 1:
                        (cx, cy) = (x, s) if horizontal else (s, y)
                        cword = crow[s:e].replace(' ', ch)
                        total_points += self.calc_word_points(cword, cx, cy, not horizontal, False)

            word_points += letter_points
            x += dx
            y += dy

        total_points += word_points * word_multiplicator

        if tiles_used >= 7:
            total_points += 40

        return total_points

    def calc_all_word_scores(self, letters, wordlist, variant=1):
        '''Calculates the score for each possible word and returns them as a list
        where each element is on the form (x, y, horizontal, word, score)
        :param letters The letters that can be used to form a word, * for wildcard
        :param wordlist The wordlist of legal words as a wordsolver.wordlist.Wordlist object'''
        for (i, row) in enumerate(self.horizontal):
            sw = list(self.surrounding_words(True, i))
            chars = [wordlist.get_legal_characters(surrounding, variant) for surrounding in sw]
            connected = [surrounding != ' ' for surrounding in sw]
            if i == 7:
                connected[7] = True
            yield from ((x, i, True, word, self.calc_word_points(word, x, i, True)) for
                        (x, word) in wordlist.words(row, list(zip(chars, connected)), letters, variant))
        for (i, row) in enumerate(self.vertical):
            sw = list(self.surrounding_words(False, i))
            chars = [wordlist.get_legal_characters(surrounding, variant) for surrounding in sw]
            connected = [surrounding != ' ' for surrounding in sw]
            if i == 7:
                connected[7] = True
            yield from ((i, y, False, word, self.calc_word_points(word, i, y, False)) for
                        (y, word) in wordlist.words(row, list(zip(chars, connected)), letters, variant))

    def __repr__(self):
        return '\n'.join(row.replace(' ', '·') for row in self.horizontal)
