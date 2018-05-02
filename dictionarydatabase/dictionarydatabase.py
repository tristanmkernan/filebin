from nltk.corpus import wordnet
from random import choice


class Dictionary(object):
    def __init__(self):
        def good_word(w):
            return len(w) in {7, 8, 9, 10} and all(c.isalpha() for c in w)

        self.valid_words = {w.lower()
                            for w in wordnet.words() if good_word(w)}

    def random_word(self, exclude):
        return choice(list(self.valid_words.symmetric_difference(exclude)))

    def define(self, word):
        syns = wordnet.synsets(word)
        return syns[0].definition()
