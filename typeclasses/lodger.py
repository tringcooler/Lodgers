# -*- coding: utf-8 -*-

from time import time
from evennia import create_object
from typeclasses.characters import Character

class Lodger(Character):

    def at_object_creation(self):
        self.db.property = {
            'attention_max': 0
            'attention_regen': 0
            }
        self.db.ability = {}
        self.db.status = {
            'attention': (0, 0, None)
            }

    def set_attention(self, val, target = None):
        self.db.status['attention'] = (val, time(), target)

    def get_attention(self):
        if not 'attention' in self.db.status:
            return 0
        val, stamp, _t = self.db.status['attention']
        timedif = max(int(time() - stamp), 0)
        new_val = min(val + timedif * self.db.property['attention_regen'],
                      self.db.property['attention_max'])

    def pay_attention(self, val, target, force = False):
        _t, _t, o_target = self.db.status['attention']
        if target == o_target:
            attention = self.db.property['attention_max']
        else:
            attention = self.get_attention()
        if attention < val and not force:
            return False
        attention -= val
        self.set_attention(attention, target)
        return True
        
class LodgerAction(object):

    def __init__(self):
        pass

