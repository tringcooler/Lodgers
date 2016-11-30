# -*- coding: utf-8 -*-

from evennia import create_object

from typeclasses.exits import Exit
from typeclasses.rooms import Room
from typeclasses.objects import Object as BaseObject

class LodgeDoor(Exit):

    def at_first_save(self):
        super(LodgeDoor, self).at_first_save()
        self.db.near = self.destination

class LodgeRoom(Room):
    
    def at_object_creation(self):
        self.db.flo = None
        self.db.pos = None
        self.db.siz = None
        self.db.instance = None

    def set_position(self, left, top, floor = 1):
        self.db.flo = floor
        self.db.pos = (left, top)

    def set_size(self, width, height):
        self.db.siz = (width, height)

    def calc_rightbottom(self):
        return self.db.pos[0] + self.db.siz[0], self.db.pos[1] + self.db.siz[1]

    def calc_distance(self, dst):
        sl = self.db.pos[0]
        st = self.db.pos[1]
        sr = sl + self.db.siz[0]
        sb = st + self.db.siz[1]
        dl = dst.db.pos[0]
        dt = dst.db.pos[1]
        dr = dl + dst.db.siz[0]
        db = dt + dst.db.siz[1]

        xd1 = max(dl - sr + 1, 0)
        xd2 = max(sl - dr + 1, 0)
        yd1 = max(dt - sb + 1, 0)
        yd2 = max(st - db + 1, 0)
        zd = abs(dst.db.flo - self.db.flo)

        distance = xd1 + xd2 + yd1 + yd2 + zd
        return distance

    def check_adjoin(self, dst):
        if self.db.pos[0] + self.db.siz[0] > dst.db.pos[0] \
           and self.db.pos[1] + self.db.siz[1] > dst.db.pos[1] \
           and dst.db.pos[0] + dst.db.siz[0] > self.db.pos[0] \
           and dst.db.pos[1] + dst.db.siz[1] > self.db.pos[1]:
            raise RuntimeError('room overlapped')
        if self.db.pos[0] + self.db.siz[0] == dst.db.pos[0]:
            st = max(self.db.pos[1], dst.db.pos[1])
            ed = min(self.db.pos[1] + self.db.siz[1],
                     dst.db.pos[1] + dst.db.siz[1])
            ln = ed - st
            if not ln > 0:
                return None
            return 'r', st, ln
        elif self.db.pos[1] + self.db.siz[1] == dst.db.pos[1]:
            st = max(self.db.pos[0], dst.db.pos[0])
            ed = min(self.db.pos[0] + self.db.siz[0],
                     dst.db.pos[0] + dst.db.siz[0])
            ln = ed - st
            if not ln > 0:
                return None
            return 'b', st, ln
        elif dst.db.pos[0] + dst.db.siz[0] == self.db.pos[0]:
            st = max(self.db.pos[1], dst.db.pos[1])
            ed = min(self.db.pos[1] + self.db.siz[1],
                     dst.db.pos[1] + dst.db.siz[1])
            ln = ed - st
            if not ln > 0:
                return None
            return 'l', st, ln
        elif dst.db.pos[1] + dst.db.siz[1] == self.db.pos[1]:
            st = max(self.db.pos[0], dst.db.pos[0])
            ed = min(self.db.pos[0] + self.db.siz[0],
                     dst.db.pos[0] + dst.db.siz[0])
            ln = ed - st
            if not ln > 0:
                return None
            return 't', st, ln
        else:
            return None

    def link_with_exit(self, dst, aliases = [], back_aliases = [], exit_typeclass = LodgeDoor):
        if self.check_adjoin(dst) == None:
            raise RuntimeError('rooms not adjoin')

        for ext in self.exits:
            if ext.destination == dst:
                return
        if self.db.instance:
            self.db.instance.create_object(exit_typeclass,
                          key = dst.key,
                          aliases = dst.aliases.all() + aliases,
                          location = self,
                          destination = dst)
            self.db.instance.create_object(exit_typeclass,
                          key = self.key,
                          aliases = self.aliases.all() + back_aliases,
                          location = dst,
                          destination = self)
        else:
            create_object(exit_typeclass,
                          key = dst.key,
                          aliases = dst.aliases.all() + aliases,
                          location = self,
                          destination = dst)
            create_object(exit_typeclass,
                          key = self.key,
                          aliases = self.aliases.all() + back_aliases,
                          location = dst,
                          destination = self)

    def on_trigger(self, info):
        return info

class util_inf_array(object):
    def __init__(self, empty_elem = None):
        self._ar = []
        self._ee = empty_elem
    def set_elem(self, pos, val):
        ar = self._ar
        dim = len(pos) - 1
        for i in pos:
            if i >= len(ar):
                for j in range(i - len(ar) + 1):
                    if dim < 1:
                        elem = self._ee
                    else:
                        elem = []
                        for k in range(dim - 1):
                            elem = [elem]
                    ar.append(elem)
            last_ar = ar
            ar = ar[i]
            dim -= 1
        last_ar[i] = val
    def get_elem(self, pos):
        ar = self._ar
        for i in pos:
            if i >= len(ar):
                return self._ee
            ar = ar[i]
        return ar
    def ar(self):
        return self._ar
    def __getitem__(self, i):
        return self._ar[i]

def draw_map(rooms, tars = [], syms = [], colors = []):
    drawn_room = []
    ar_map = util_inf_array(empty_elem = ' ')

    def trans_pos(pos, shift = (0, 0)):
        return pos[1] * 2 + shift[1], pos[0] * 4 + shift[0]

    def calc_mid(st, ln):
        return st + int(ln/2)

    def draw_sym(pos, sym, shift=(0, 0), match=' ', force=False):
        ar_pos = trans_pos(pos, shift)
        old_sym = ar_map.get_elem(ar_pos)
        colored = False
        if len(old_sym) > 2:
            old_sym = old_sym[-3]
        if len(sym) > 2 and sym[-3] == old_sym:
            colored = True
        if force or old_sym == match or colored:
            ar_map.set_elem(ar_pos, sym)

    def draw_room(room):
        left, top = room.db.pos
        right, bottom = room.calc_rightbottom()

        sym = None
        color = None
        if room in tars:
            idx = tars.index(room)
            sym = syms[idx]
            if not sym:
                color = colors[idx]
            midx = calc_mid(left, room.db.siz[0])
            midy = calc_mid(top, room.db.siz[1])

        def clsym(s):
            if color:
                return '{' + color + s + '{n'
            else:
                return s

        for i in range(left, right):
            for j in range(4):
                draw_sym((i, top), clsym('-'), (j, 0))
        draw_sym((left, top), clsym('+'), force=True)
        for i in range(top, bottom):
            for j in range(2):
                draw_sym((right, i), clsym('|'), (0, j))
        draw_sym((right, top), clsym('+'), force=True)
        for i in range(right, left, -1):
            for j in range(4):
                draw_sym((i, bottom), clsym('-'), (-j, 0))
        draw_sym((right, bottom), clsym('+'), force=True)
        for i in range(bottom, top, -1):
            for j in range(2):
                draw_sym((left, i), clsym('|'), (0, -j))
        draw_sym((left, bottom), clsym('+'), force=True)
        
        if sym:
            color = colors[idx]
            draw_sym((midx, midy), clsym(sym), (2, 1))

    def draw_door(room, dst):
        ret = room.check_adjoin(dst)
        if ret == None:
            raise RuntimeError('rooms not adjoin')
        dr, st, ln = ret
        left, top = room.db.pos
        right, bottom = room.calc_rightbottom()
        mid = calc_mid(st, ln)
        
        if dr == 't':
            draw_sym((mid, top), '#', (2, 0), '-')
        elif dr == 'b':
            draw_sym((mid, bottom), '#', (2, 0), '-')
        elif dr == 'l':
            draw_sym((left, mid), '#', (0, 1), '|')
        elif dr == 'r':
            draw_sym((right, mid), '#', (0, 1), '|')
    
    def draw(room, drawn):
        if not room in rooms:
            return
        if room in drawn_room:
            return
        draw_room(room)
        drawn.append(room)
        for ext in room.exits:
            dst = ext.destination
            draw_door(room, dst)
            draw(dst, drawn)

    for room in rooms:
        draw(room, drawn_room)
    rar = ar_map.ar()
    rstr = '\n'.join([''.join(i) for i in rar])

    return rstr

class LodgeInstance(BaseObject):

    def at_object_creation(self):
        self.db.rooms = []
        self.db.log = None
        self.db.inst_tag = self.key

    def get_tag(self):
        if not self.db.inst_tag:
            raise RuntimeError('instance tag invalid')
        return self.db.inst_tag

    def get_room_tag(self):
        return self.get_tag() + '@room'

    def get_obj_tag(self):
        return self.get_tag() + '@obj'

    def get_log_tag(self):
        return self.get_tag() + '@log'

    def create_object(self, *args, **kargs):
        obj = create_object(*args, **kargs)
        obj.tags.add(self.get_obj_tag(), category='instance')
        return obj

    def create_room(self, *args, **kargs):
        roomdict = {}
        if 'position' in kargs:
            roomdict['pos'] = kargs['position']
            del kargs['position']
        if 'size' in kargs:
            roomdict['siz'] = kargs['size']
            del kargs['size']
        if 'floor' in kargs:
            roomdict['flo'] = kargs['floor']
            del kargs['floor']
        else:
            roomdict['flo'] = 1
        room = create_object(LodgeRoom, *args, **kargs)
        room.db.instance = self
        for k in roomdict:
            setattr(room.db, k, roomdict[k])
        room.tags.add(self.get_room_tag(), category='instance')
        self.db.rooms.append(room)
        return room

    def add_room(self, room):
        if not room in self.db.rooms:
            room.db.instance = self
            room.tags.remove(category='instance')
            room.tags.add(self.get_room_tag(), category='instance')
            self.db.rooms.append(room)

    
