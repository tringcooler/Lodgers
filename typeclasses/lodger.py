# -*- coding: utf-8 -*-

from time import time as get_time
from evennia import create_object
from typeclasses.characters import Character

class Lodger(Character):

    def at_object_creation(self):
        self.db.property = {
            'attention_max': 0,
            'attention_regen': 0,
            }
        self.db.ability = {}
        self.db.status = {
            'attention_pool': (0, 0, None),
            'attention_locked': ([], []),
            }

    def _set_attention_pool(self, val, target = None, time = None):
        if not time:
            time = get_time()
        self.db.status['attention_pool'] = (val, time, target)

    def _get_attention_pool(self, time = None):
        if not time:
            time = get_time()
        val, stamp, _t = self.db.status['attention_pool']
        timedif = max(int(time - stamp), 0)
        new_val = min(val - timedif * self.db.property['attention_regen'], 0)
        return new_val

    def _set_attention_locked(self, val, target):
        attention_locked = self.db.status['attention_locked']
        if target in attention_locked[0]:
            idx = attention_locked[0].index(target)
        else:
            idx = len(attention_locked[0])
            attention_locked[0].append(target)
            attention_locked[1].append(0)
        attention_locked[1][idx] += val
        if attention_locked[1][idx] <= 0:
            del attention_locked[0][idx]
            del attention_locked[1][idx]

    def _set_attention_locked(self, val, target):
        attention_locked = self.db.status['attention_locked']
        if not target in attention_locked[0]:
            return 0
        idx = attention_locked[0].index(target)
        return attention_locked[1][idx]

    def pay_attention(self, val, target, force = False):
        _t, _t, o_target = self.db.status['attention']
        if target == o_target:
            attention = self.db.property['attention_max']
        else:
            attention = self.get_attention()
        if attention < val and not force:
            return False
        attention = max(attention - val, 0)
        self.set_attention(attention, target)
        return True
        
class LodgerAction(object):

    def __init__(self):
        self.attention = 0
        self.positive = True
        self.triger = None

    def execute(self, caller, target):
        if not caller.pay_attention(
            self.attention, target, self.positive):
            return False
