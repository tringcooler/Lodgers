# -*- coding: utf-8 -*-

from time import time as get_time
from evennia import create_object, search_object
from typeclasses.characters import Character
from typeclasses.objects import Object as BaseObject
from commands.command import Command

class Lodger(Character):

    def at_object_creation(self):
        self.db.property = {
            'attention_max': 0,
            'attention_regen': 0,
            }
        self.db.ability = {
            'auto_reaction': {},
            }
        self.db.status = {
            'attention_pool': (0, 0, None),
            'attention_locked': {},
            'action_handle': {
                'eye': None,
                'ear': None,
                'mouth': None,
                'hand': None,
                'foot': None,
                },
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

    def check_attention(self, target, time = None):
        attention = self._get_attention_pool_max()
        attention += self._get_attention_locked(target)
        attention_pool, o_target = self._get_attention_pool(time = time)
        if target != o_target:
            attention -= attention_pool
        return attention

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

    def on_trigger(self, info):
        pass

    def feel(source, content):
        self.msg('{0}:{1}'.format(source, content))
        
class LodgerAction(object):

    desc = None
    trigger_room_only = False
    trigger_volume = 0
    trigger_volume_reduce = 10

    def __init__(self):
        pass
    
    def description(self):
        if self.desc:
            return self.desc
        else:
            return self

    def on_trigger(self, info):
        info['volum'] = max(0,
            self.trigger_volume - self.trigger_volume_reduce * info['distance'])
        return info

    def on_reaction(self, action, caller, info):
        pass

    def trigger(self, caller):
        s_room = caller.location
        lodge = s_room.db.instance
        for room in lodge.db.rooms:
            info = {
                'caller': caller,
                'action': self.description(),
                }
            if room == s_room:
                info['distance'] = 0
            else:
                if self.trigger_room_only:
                    continue
                info['distance'] = room.calc_distance(s_room)
            info = self.on_triggrt(info)
            if room != s_room:
                info['source'] = s_room
                info['destination'] = room
                info = s_room.on_trigger(info)
                info = room.on_trigger(info)
            for obj in room.contents:
                if hasattr(obj, 'on_trigger'):
                    obj.on_trigger(info)

    def reaction(self, action, caller, info):
        return self.on_reaction(action, caller, info)

    def execute(self, caller, info):
        pass

TXT_ACTION_CN = {
    'look': {
        'error': {
            'nothing': '不知道应该看向哪里',
            }
        }
    }
TXT_ACTION = TXT_ACTION_CN

class LookAction(LodgerAction):
    
    desc = 'look'
    trigger_room_only = True

    def __init__(self):
        super(LodgerAction, self).__init__()

    def on_reaction(self, action, caller, info):
        if action == 'look':
            pass

    def execute(self, caller, info):
        if not 'target' in info:
            caller.feel('error', TXT_ACTION['look']['error']['nothing'])
            return
        target = info['target']
        pass
        caller.feel('look', content)

g_action_list_key = None
def create_action_list(key):
    if g_action_list_key:
        raise RuntimeError('action list already exist')
    al = create_object(LodgeActionList, key = key)
    g_action_list_key = key
    return al

def get_action_list():
    if not g_action_list_key:
        raise RuntimeError('action list not exist')
    return search_object(g_action_list_key)[0]

def get_action(desc):
    return get_action_list().get_action(desc)
        
class LodgeActionList(BaseObject):

    def at_object_creation(self):
        self.db.actions = {}

    def create_action(self, action):
        if action.desc in self.db.actions:
            raise RuntimeError('action already exist')
        self.db.actions[action.desc] = action()

    def get_action(self, desc):
        return self.db.actions[desc]

