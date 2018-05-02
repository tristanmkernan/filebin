from flask import session
from functools import wraps

import time


def purge_expired():
    # manage session for browser-based visitors
    # history items are two-item tuples like (code, expiration timestamp)
    history = []
    history_code_cache = set()

    for fb in session.get('history', []):
        if fb[1] - time.time() > 0:
            history.append(fb)
            history_code_cache.add(fb[0])

    return history, history_code_cache


def maintain_history(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        history, _ = purge_expired()
        session['history'] = history

        return f(*args, **kwargs)

    return wrapped


class HistoryManager(object):
    def __init__(self, filestore):
        self.filestore = filestore

    def add(self, code):
        # manage session for browser-based visitors
        # history items are two-item tuples like (code, expiration timestamp)
        history, history_code_cache = purge_expired()

        if code not in history_code_cache:
            try:
                filebin = self.filestore.access(code)

                history.insert(
                    0,
                    (code, filebin.meta.expiration_timestamp_utc)
                )

                session['history'] = history
            except:
                pass
