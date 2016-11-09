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
        new_val = max(val - timedif * self.db.property['attention_regen'], 0)
        return new_val, target

    def _set_attention_locked(self, val, target):
        attention_locked = self.db.status['attention_locked']
        if not target in attention_locked:
            attention_locked[target] = 0
        attention_locked[target] += val
        if attention_locked[target] <= 0:
            val -= attention_locked[target]
            del attention_locked[target]
        return val

    def _get_attention_locked_all(self):
        attention_locked = self.db.status['attention_locked']
        attention = 0
        for target in attention_locked:
            attention += attention_locked[target]
        return attention

    def _get_attention_locked(self, target):
        attention_locked = self.db.status['attention_locked']
        if not target in attention_locked:
            return 0
        return attention_locked[target]

    def _get_attention_pool_max(self):
        return max(
            self.db.property[
                'attention_max'] - self._get_attention_locked_all()
            , 0)

    def pay_attention(self, val, target, force = False, time = None):
        # |            attention           |
        # |      used      |               |
        # |       target == o_target :     |
        # |  val  |        |               |
        # |        val          |          |
        # |       target != o_target :     |
        # |                |   val    |    |
        if val <= 0:
            return True
        attention = self._get_attention_pool_max()
        if attention == 0 and not force:
            return False
        attention_locked = self._get_attention_locked(target)
        attention_pool, o_target = self._get_attention_pool(time = time)
        attention_used = attention_locked + attention_pool
        if target == o_target:
            val = max(val - attention_used, 0)
        else:
            val = max(val - attention_locked, 0)
        cost = val + attention_pool
        if attention < cost and not force:
            return False
        cost = min(cost, attention)
        self._set_attention_pool(cost, target, time = time)
        return True

    def lock_attention(self, val, target, force = False, time = None):
        if val <= 0:
            return True
        attention = self._get_attention_pool_max()
        if attention == 0 and not force:
            return False
        attention_pool, o_target = self._get_attention_pool(time = time)
        if target == o_target:
            remain = max(attention_pool - val, 0)
        else:
            remain = min(attention_pool,
                         max(attention - val, 0))
            attention -= attention_pool
        if attention < val and not force:
            return False
        self._set_attention_pool(remain, target = None, time = time)
        self._set_attention_locked(val, target)
        return True

    def free_attention(self, val, target, time = None):
        if val <= 0:
            return
        val = - self._set_attention_locked(- val, target)
        attention = self._get_attention_pool_max()
        attention_pool, _t = self._get_attention_pool(time = time)
        val += attention_pool
        val = min(val, attention)
        self._set_attention_pool(val, target, time = time)
        
class LodgerAction(object):

    def __init__(self):
        self.attention = 0
        self.positive = True
        self.triger = None

    def execute(self, caller, target):
        if not caller.pay_attention(
            self.attention, target, self.positive):
            return False
        
        

