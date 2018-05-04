import json
import os

fpath = "data/state.json"


class State(object):
    def __init__(self):
        self._state = dict()

    def get(self, key):
        return self._state.get(key)

    def update(self, key, value):
        self._state.update({key: value})
        self.save()

    def save(self):
        with open(fpath, "w") as f:
            json.dump(self._state, f)

    @classmethod
    def load(self):
        s = State()
        if os.path.exists(fpath):
            with open(fpath) as f:
                s._state = json.load(f)
        return s
