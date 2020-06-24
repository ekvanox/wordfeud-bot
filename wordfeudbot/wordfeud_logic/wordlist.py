# -*- coding: utf-8 -*-

# (c) 2011, Marcus Svensson <macke77@gmail.com>
# See gpl-2.0.txt for license

import logging

log = logging.getLogger('wordlist')


class Wordlist(object):

    def __init__(self):
        '''Initializes a Wordlist object. It can actually contain several wordlists
        in the same datastructure (to save memory)'''
        self.root = Node()
        self.wordfiles = []
        self.all_chars = set()
        self.word_count = 0

    def read_wordlist(self, wordfile):
        '''Reads a wordlist from a file that contains one word per line in utf-8 format
        :param wordfile The name of the file to read from'''
        if wordfile in self.wordfiles:
            log.info('%s already loaded', wordfile)
            return
        variant = 1 << len(self.wordfiles)
        with open(wordfile) as f:
            for line in f:
                word = line.lower().strip()
                if word[0] == '#':
                    log.debug('Wordlist comment: %s', word[1:])
                    continue
                self.add(word, variant)
        self.wordfiles.append(wordfile)
        return variant

    def add(self, word, variant):
        self.all_chars.update(word)
        node = self.root
        for ch in word:
            node.variants |= variant
            node = node.child(ch)
        if (node.word & variant) == 0:
            node.word |= variant
            node.variants |= variant
            self.word_count += 1

    def words(self, row, rowdata, letters, variant):
        assert (len(row) == len(rowdata)), ("%d == %d" % (len(row), len(rowdata)))
        row = row+' '
        for pos in range(len(row)-1):
            if pos > 0 and row[pos-1] != ' ':
                continue
            yield from ((pos, word) for word in self.root.matches(row, rowdata, pos, letters, variant))

    def get_legal_characters(self, word, variant):
        if word == ' ':
            return self.all_chars
        i = word.find(' ')
        m = list(self.root.matches(word+' ', [(self.all_chars, True)]*(len(word)+1), 0, '*', variant))
        return set(match[i].lower() for match in m)

    def is_word(self, word, variant=1):
        node = self.root
        try:
            for ch in word:
                node = node.children[ch]
                if (node.variants & variant) == 0:
                    return False
            return node.word
        except:
            return False

    def __repr__(self):
        return '<Worldlist: %d words from "%s">' % (self.word_count, '", "'.join(self.wordfiles))


class Node(object):

    def __init__(self):
        self.word = 0
        self.variants = 0
        self.children = {}

    def child(self, char):
        try:
            return self.children[char]
        except:
            c = Node()
            self.children[char] = c
            return c

    def has_child(self, char):
        return self.children.get(char)

    def matches(self, row, rowdata, pos, letters, variant, word='', connecting=False, extending=False):
        if pos < len(row) and (variant & self.variants) != 0:
            if row[pos] != ' ':
                child = self.children.get(row[pos].lower())
                if child:
                    yield from child.matches(row, rowdata, pos+1, letters, variant, word+row[pos], True, extending)
            else:
                if self.word and connecting and extending and len(word) > 1:
                    yield word
                if pos < len(row)-1:
                    valid_chars, connected = rowdata[pos]
                    for i, ch in enumerate(letters):
                        if not ch in valid_chars and ch != '*':
                            continue
                        if letters.find(ch, 0, i) != -1:
                            continue
                        if ch == '*':
                            # wildcard
                            next_letters = letters[:i] + letters[i+1:]
                            for wc, child in self.children.items():
                                if wc in valid_chars:
                                    yield from child.matches(row, rowdata, pos+1, next_letters, variant, word+wc.upper(), connecting or connected, True)
                        child = self.children.get(ch)
                        if child:
                            yield from child.matches(row, rowdata, pos+1, letters[:i] + letters[i+1:], variant, word+ch, connecting or connected, True)
