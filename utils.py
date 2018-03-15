import json
import os
import random


# thanks to https://stackoverflow.com/a/1094933
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def _good_word(w):
    if len(w) in (7, 8, 9, 10):
        if all(map(str.isalpha, w)):
            return w


class DictionaryDatabase(object):
    def __init__(self):
        self.words_db = json.load(open(os.path.join(os.path.dirname(__file__), './data/dictionary/dictionary.json')))
        self.words_db = {k.lower(): v for k, v in self.words_db.items() if _good_word(k)}
        self.words_list = [k for k in self.words_db.keys()]

    def random_word(self):
        return self.words_list[ random.randint(0, len(self.words_list)) ]

    def define(self, word):
        return self.words_db.get(word, None)
