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
            'trigger_volume': 0,
            }
        self.db.ability = {
            'action': {
                'look_and_listen': 'look',
                'look': 'look',
                'listen': 'listen',
                },
            'reaction': {},
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

    def pay_attention(
        self, target, payment, threshold = None, force = False, time = None):
        # |            attention           |
        # |      used      |               |
        # |       target == o_target :     |
        # |  val  |        |               |
        # |        val          |          |
        # |       target != o_target :     |
        # |                |   val    |    |
        if threshold == None:
            threshold = payment
        if threshold <= 0 and payment <= 0:
            return True
        attention_pool = self._get_attention_pool_max()
        attention_locked = self._get_attention_locked(target)
        attention_remain = attention_pool + attention_locked
        attention_pool_used, o_target = self._get_attention_pool(time = time)
        if target == o_target:
            attention_used = attention_locked + attention_pool_used
        else:
            attention_used = attention_locked
            attention_remain -= attention_pool_used
        if attention_remain < threshold and not force:
            return False
        payment = max(payment - attention_used, 0)
        payment = min(payment + attention_pool_used, attention_pool)
        self._set_attention_pool(payment, target, time = time)
        return True

    def check_attention(self, target, time = None):
        attention = self._get_attention_pool_max()
        attention += self._get_attention_locked(target)
        attention_pool, o_target = self._get_attention_pool(time = time)
        if target != o_target:
            attention -= attention_pool
        self.dbgmsg('check: {0} has {1} att'.format(target.name, attention))
        return attention

    def lock_attention(self, target, val, force = False, time = None):
        if val <= 0:
            return True
        attention = attention_pool_max = self._get_attention_pool_max()
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
        val = min(val, attention_pool_max)
        self._set_attention_pool(remain, target = None, time = time)
        self._set_attention_locked(val, target)
        return True

    def free_attention(self, target, val, time = None):
        if val <= 0:
            return
        val = - self._set_attention_locked(- val, target)
        attention = self._get_attention_pool_max()
        attention_pool, _t = self._get_attention_pool(time = time)
        val += attention_pool
        val = min(val, attention)
        self._set_attention_pool(val, target, time = time)

    def on_trigger(self, action, caller, info):
        seen = False
        heard = False
        if ('visible' in info) and info['visible']:
            seen = True
        if ('volume' in info) and (
            info['volume'] >= self.db.property['trigger_volume']):
            heard = True
        a_info = {
            'target': caller,
            'action': action,
            }
        if 'trigger_history' in info:
            a_info['trigger_history'] = info['trigger_history']
        if 'action_info' in info:
            a_info['action_info'] = info['action_info']
            if 'attention_time' in info['action_info']:
                a_info['attention_time'] = info['action_info']['attention_time']
        def trigger_act(act):
            if not hasattr(act, 'on_trigger') or (
                act.on_trigger(self, caller, info)):
                act.execute(self, a_info)
        if seen and heard and (
            'look_and_listen' in self.db.ability['action']):
            act = G_ACT(self.db.ability['action']['look_and_listen'])
            trigger_act(act)
        else:
            if seen and 'look' in self.db.ability['action']:
                act = G_ACT(self.db.ability['action']['look'])
                trigger_act(act)
            if heard and 'listen' in self.db.ability['action']:
                act = G_ACT(self.db.ability['action']['listen'])
                trigger_act(act)
        if action in self.db.ability['reaction']:
            act = G_ACT(self.db.ability['reaction'][action])
            trigger_act(act)

    def feel(self, source, content):
        self.msg('{0}:{1}'.format(source, content))

    def dbgmsg(self, content):
        self.feel('debug', content)
        
class LodgerAction(object):

    desc = None
    trigger_room_only = True
    trigger_volume = 0
    trigger_volume_reduce = 10
    attention_payment = 0

    def __init__(self):
        pass
    
    def description(self):
        if self.desc:
            return self.desc
        else:
            return self

    def has_reaction(self, action, info):
        reaction_name = 'on_reaction_' + action
        if 'action' in info:
            if hasattr(info['action'], reaction_name):
                return getattr(info['action'], reaction_name)
        elif 'target' in info:
            if hasattr(info['target'], reaction_name):
                return getattr(info['target'], reaction_name)
        return None

    #def on_trigger(self, trigger, caller, info):
    #    return True

    def trigger_prepare(self, caller, info):
        info['volume'] = max(0,
            self.trigger_volume - self.trigger_volume_reduce * info['distance'])
        if info['distance'] == 0:
            info['visible'] = True
        else:
            info['visible'] = False
        return info

    def trigger_summary(self, caller, info):
        return (self.description(), caller)

    def trigger(self, caller, info):
        s_room = caller.location
        lodge = s_room.db.instance
        summary = self.trigger_summary(caller, info)
        if 'trigger_history' in info:
            if summary in info['trigger_history']:
                return
            trigger_history = list(info['trigger_history'])
            trigger_history.append(summary)
        else:
            trigger_history = [summary]
        for room in lodge.db.rooms:
            t_info = {
                'action_info': info,
                'trigger_history': trigger_history,
                }
            action = self.description()
            if room == s_room:
                t_info['distance'] = 0
            else:
                if self.trigger_room_only:
                    continue
                t_info['distance'] = room.calc_distance(s_room)
            t_info = self.trigger_prepare(caller, t_info)
            if room != s_room:
                t_info['source'] = s_room
                t_info['destination'] = room
                t_info = s_room.on_trigger(action, caller, t_info)
                t_info = room.on_trigger(action, caller, t_info)
            for obj in room.contents:
                if hasattr(obj, 'on_trigger'):
                    obj.on_trigger(action, caller, t_info)

    def attention(self, caller, info, payment = None, threshold = None):
        if 'attention_force' in info:
            force = info['attention_force']
        else:
            force = False
        if 'attention_time' in info:
            time = info['attention_time']
        else:
            time = None
        if payment == None:
            payment = self.attention_payment
        if 'target' in info:
            return caller.pay_attention(
                info['target'], payment, threshold,
                force = force, time = time)
        return False

    def execute(self, caller, info):
        pass

LIST_ACTION = {}
def C_ACT(act):
    if act.desc in LIST_ACTION:
        raise RuntimeError('action already exist')
    LIST_ACTION[act.desc] = act()
def G_ACT(desc):
    return LIST_ACTION[desc]

TXT_ACTION_CN = {
    'look': {
        'reaction': {
            'look': '看见{0}正看向{1}',
            },
        'error': {
            'nothing': '不知道应该看向哪里',
            },
        },
    }
TXT_ACTION = TXT_ACTION_CN

class LookAction(LodgerAction):
    
    desc = 'look'
    attention_payment = 10

    def __init__(self):
        super(LodgerAction, self).__init__()

    def on_reaction_look(self, caller, info):
        att_payment = 10
        att_threshold = 100
        if not self.attention(caller, info, att_payment, att_threshold):
            return
        target = info['target']
        patt = TXT_ACTION['look']['reaction']['look']
        content = patt.format(caller.name, target.name)
        caller.feel('look', content)
        self.trigger(caller, info)
    
    def execute(self, caller, info):
        if not 'target' in info:
            caller.feel('error', TXT_ACTION['look']['error']['nothing'])
            return
        target = info['target']
        react = self.has_reaction(self.desc, info)
        if not react:
            if self.attention(caller, info):
                content = caller.at_look(target)
                caller.feel('look', content)
                self.trigger(caller, info)
        else:
            react(caller, info)

C_ACT(LookAction)
