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
            'attention_locked': {},
            }

    def _set_attention_pool(self, val, target = None, time = None):
        if not time:
            time = get_time()
        if not target:
            _t, _t, target = self.db.status['attention_pool']
        self.db.status['attention_pool'] = (val, time, target)

    def _get_attention_pool(self, time = None):
        val, stamp, target = self.db.status['attention_pool']
        if not time:
            time = get_time()
        timedif = max(int(time - stamp), 0)
        new_val = min(val - timedif * self.db.property['attention_regen'], 0)
        return new_val, target

    def _set_attention_locked(self, val, target):
        attention_locked = self.db.status['attention_locked']
        if not target in attention_locked:
            attention_locked[target] = 0
        attention_locked[target] += val
        if attention_locked[target] <= 0:
            del attention_locked[target]

    def _get_attention_locked_all(self):
        attention = 0
        for target in attention_locked:
            attention += attention_locked[target]
        return attention

    def _get_attention_locked(self, target):
        attention_locked = self.db.status['attention_locked']
        if not target in attention_locked:
            return 0
        return attention_locked[target]

    def _calc_attention_cost(self, val, target, time = None):
        # |              pool              |
        # |      used      |               |
        # |       target == o_target :     |
        # |  val  | remain |               |
        # |        val          |          |
        # |       target != o_target :     |
        # |     remain     |   val    |    |
        attention = self.db.property['attention_max']
        attention -= self._get_attention_locked_all()
        attention += self._get_attention_locked(target)
        attention_used, o_target = self._get_attention_pool(time = time)
        if target == o_target:
            cost = max(val, attention_used)
            remain = min(attention_used - val, 0)
        else:
            cost = val + attention_used
            remain = attention_used
        return attention, cost, remain

    def pay_attention(self, val, target, force = False, time = None):
        attention, cost, _t = self._calc_attention_cost(val, target, time = time)
        if attention < cost and not force:
            return False
        cost = min(cost, attention)
        self._set_attention_pool(cost, target, time = time)
        return True

    def lock_attention(self, val, target, force = False, time = None):
        attention, cost, remain = self._calc_attention_cost(val, target, time = time)
        if attention < cost and not force:
            return False
        pass

    def free_attention(self, val, target, force = False, time = None):
        pass
        
class LodgerAction(object):

    def __init__(self):
        self.attention = 0
        self.positive = True
        self.triger = None

    def execute(self, caller, target):
        if not caller.pay_attention(
            self.attention, target, self.positive):
            return False
        
        

