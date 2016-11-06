# -*- coding: utf-8 -*-

from evennia import create_object
from typeclasses.lodge import LodgeInstance

def build_the1st_lodge():

    lodge = create_object(LodgeInstance, key = 'lodge01')
    
    hall = lodge.create_room(key = 'hall',
                             position = (3, 3),
                             size = (7, 5))
    
    passage_l = lodge.create_room(key = 'left passage',
                                  position = (2, 3),
                                  size = (1, 5))

    passage_r = lodge.create_room(key = 'right passage',
                                  position = (10, 0),
                                  size = (1, 8))

    passage_m = lodge.create_room(key = 'middle passage',
                                  position = (3, 2),
                                  size = (7, 1))

    room_1 = lodge.create_room(key = 'room 1', aliases = ['r1'],
                               position = (0, 7),
                               size = (2, 1))

    room_2 = lodge.create_room(key = 'room 2', aliases = ['r2'],
                               position = (0, 3),
                               size = (2, 4))

    room_3 = lodge.create_room(key = 'room 3', aliases = ['r3'],
                               position = (0, 0),
                               size = (3, 3))

    room_4 = lodge.create_room(key = 'room 4', aliases = ['r4'],
                               position = (3, 0),
                               size = (4, 2))

    room_5 = lodge.create_room(key = 'room 5', aliases = ['r5'],
                               position = (7, 0),
                               size = (3, 2))

    room_6 = lodge.create_room(key = 'room 6', aliases = ['r6'],
                               position = (11, 0),
                               size = (2, 8))

    hall.link_with_exit(passage_l, aliases = ['left'])
    hall.link_with_exit(passage_r, aliases = ['right'])
    hall.link_with_exit(passage_m, aliases = ['middle', 'mid'])

    passage_l.link_with_exit(room_1, back_aliases = ['out'])
    passage_l.link_with_exit(room_2, back_aliases = ['out'])
    passage_l.link_with_exit(room_3, back_aliases = ['out'])

    room_3.link_with_exit(room_4)
    passage_m.link_with_exit(room_4, back_aliases = ['out'])
    passage_m.link_with_exit(room_5, back_aliases = ['middle', 'mid'])

    passage_m.link_with_exit(passage_r,
                             aliases = ['right'],
                             back_aliases = ['middle', 'mid'])
    passage_r.link_with_exit(room_5, back_aliases = ['right'])
    passage_r.link_with_exit(room_6, back_aliases = ['out'])
    

#batch to make the lodge
build_the1st_lodge()
