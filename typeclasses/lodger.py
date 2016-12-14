# -*- coding: utf-8 -*-

from time import time as get_time
from evennia import create_object, search_object
from evennia import CmdSet
from typeclasses.characters import Character
from typeclasses.objects import Object as BaseObject
from commands.command import Command as BaseCommand

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
                #'listen': 'listen',
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

    def at_cmdset_get(self, **kwargs):
        if "force_init" in kwargs or not self.cmdset.has_cmdset(
            'lodger_base_cmdset'):
            self.cmdset.add(
                LodgerCmdSetGen(
                    self.db.ability['action'].keys(),
                    'lodger_base_cmdset'),
                permanent=False)

    def at_init(self):
        self.cmdset.remove('lodger_base_cmdset')

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
        self.dbgmsg('pay_att: while has {2} att, pay {1} att for {0}'.format(
            self.dbgname(target), payment, threshold))
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
        self.dbgmsg(
            'pay_att: {1} att remain for {0}, {3} att for {2} in pool'.format(
                self.dbgname(target), attention_remain,
                self.dbgname(o_target), attention_pool_used))
        if attention_remain < threshold and not force:
            return False
        payment = max(payment - attention_used, 0)
        payment = min(payment + attention_pool_used, attention_pool)
        self._set_attention_pool(payment, target, time = time)
        self.dbgmsg('pay_att: after pay, {1} att for {0} in pool'.format(
            self.dbgname(target), payment))
        return True

    def check_attention(self, target, time = None):
        attention = self._get_attention_pool_max()
        attention += self._get_attention_locked(target)
        attention_pool, o_target = self._get_attention_pool(time = time)
        if target != o_target:
            attention -= attention_pool
        self.dbgmsg('chk_att: {1} att remain for {0}'.format(
            self.dbgname(target), attention))
        return attention

    def lock_attention(self, target, val, force = False, time = None):
        self.dbgmsg('lck_att: lock {1} att for {0}'.format(
            self.dbgname(target), val))
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
        self.dbgmsg(
            'lck_att: after lock, {1} att for {0} in pool, {3} att locked for {2}'.format(
                self.dbgname(o_target), remain, target.name, val))
        return True

    def free_attention(self, target, val, time = None):
        self.dbgmsg('fre_att: free {1} att for {0}'.format(
            self.dbgname(target), val))
        if val <= 0:
            return
        val = - self._set_attention_locked(- val, target)
        attention = self._get_attention_pool_max()
        attention_pool, _t = self._get_attention_pool(time = time)
        val += attention_pool
        val = min(val, attention)
        self._set_attention_pool(val, target, time = time)
        self.dbgmsg('fre_att: after free, {1} att for {0} in pool'.format(
            self.dbgname(target), val))

    def get_act(self, action, group = 'action'):
        return G_ACT(self.db.ability[group][action])

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
            act = self.get_act('look_and_listen')
            trigger_act(act)
        else:
            if seen and 'look' in self.db.ability['action']:
                act = self.get_act('look')
                trigger_act(act)
            if heard and 'listen' in self.db.ability['action']:
                act = self.get_act('listen')
                trigger_act(act)
        if action in self.db.ability['reaction']:
            act = self.get_act(action, 'reaction')
            trigger_act(act)

    def feel(self, source, content, info = None):
        self.msg('{0}:{1}'.format(source, content))

    def dbgmsg(self, content):
        self.feel('debug', content)

    def dbgname(self, obj):
        if hasattr(obj, 'name'):
            return obj.name
        else:
            return repr(obj)
        
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
        if 'target' in info:
            if 'action' in info:
                act = info['target'].get_act(info['action'])
                if hasattr(act, reaction_name):
                    return getattr(act, reaction_name)
            else:
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

    def on_cmd_create(self):
        return {
            'key': self.desc,
            'aliases': TXT_CMD_ALIASES[self.desc],
            }

    def on_parse(self, args_line):
        args = args_line.split()
        a_info = {}
        if len(args) > 0:
            targets = search_object(args[0])
            if targets:
                a_info['target'] = targets[0]
        return a_info

    def execute(self, caller, info):
        pass

class LodgerCmd(BaseCommand):

    def parse(self):
        self.act = self.obj.get_act(self.key)
        self.act_info = self.act.on_parse(self.args)

    def func(self):
        self.caller.dbgmsg('{1} {0} {2}'.format(
            self.key,
            self.caller.dbgname(self.caller),
            self.caller.dbgname(
                self.act_info['target'] if 'target' in self.act_info else None)))
        self.act.execute(self.caller, self.act_info)

class LodgerCmdSet(CmdSet):

    def at_cmdset_creation(self):
        for key in self.cmd_list:
            act = self.cmdsetobj.get_act(key)
            add_kargs = act.on_cmd_create()
            cmd = LodgerCmd(**add_kargs)
            self.add(cmd)

def LodgerCmdSetGen(actions, cmdset_key):
    class lcs(LodgerCmdSet):
        key = cmdset_key
        cmd_list = actions
    return lcs

TXT_CMD_ALIASES_CN = {
    'look': ['看', 'lk'],
    }
TXT_CMD_ALIASES = TXT_CMD_ALIASES_CN

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
        patt = TXT_ACTION[self.desc]['reaction']['look']
        content = patt.format(caller.name, target.name)
        caller.feel('look', content)
        self.trigger(caller, info)
    
    def execute(self, caller, info):
        caller.dbgmsg('look: {0} {1}: {2}'.format(
            caller.dbgname(caller),
            caller.dbgname(
                info['target'] if 'target' in info else None),
            repr(info)))
        if not 'target' in info:
            caller.feel('error', TXT_ACTION[self.desc]['error']['nothing'])
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
