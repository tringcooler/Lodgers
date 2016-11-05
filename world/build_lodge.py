
# -*- coding: utf-8 -*-

from evennia import create_object
from typeclasses.lodge import LodgeRoom

def build_the1st_lodge():
    
    hall = create_object(LodgeRoom, key = 'hall')
    hall.set_position(3, 3)
    hall.set_size(7, 5)
    hall.tags.add('lodge#1', category='instance')
    
    passage_l = create_object(LodgeRoom, key = 'left passage')
    passage_l.set_position(2, 3)
    passage_l.set_size(1, 5)
    passage_l.tags.add('lodge#1', category='instance')

    passage_r = create_object(LodgeRoom, key = 'right passage')
    passage_r.set_position(10, 0)
    passage_r.set_size(1, 8)
    passage_r.tags.add('lodge#1', category='instance')

    passage_m = create_object(LodgeRoom, key = 'middle passage')
    passage_m.set_position(3, 2)
    passage_m.set_size(7, 1)
    passage_m.tags.add('lodge#1', category='instance')

    room_1 = create_object(LodgeRoom, key = 'room 1', aliases = ['r1'])
    room_1.set_position(0, 7)
    room_1.set_size(2, 1)
    room_1.tags.add('lodge#1', category='instance')

    room_2 = create_object(LodgeRoom, key = 'room 2', aliases = ['r2'])
    room_2.set_position(0, 3)
    room_2.set_size(2, 4)
    room_2.tags.add('lodge#1', category='instance')

    room_3 = create_object(LodgeRoom, key = 'room 3', aliases = ['r3'])
    room_3.set_position(0, 0)
    room_3.set_size(3, 3)
    room_3.tags.add('lodge#1', category='instance')

    room_4 = create_object(LodgeRoom, key = 'room 4', aliases = ['r4'])
    room_4.set_position(3, 0)
    room_4.set_size(4, 2)
    room_4.tags.add('lodge#1', category='instance')

    room_5 = create_object(LodgeRoom, key = 'room 5', aliases = ['r5'])
    room_5.set_position(7, 0)
    room_5.set_size(3, 2)
    room_5.tags.add('lodge#1', category='instance')

    room_6 = create_object(LodgeRoom, key = 'room 6', aliases = ['r6'])
    room_6.set_position(11, 0)
    room_6.set_size(2, 8)
    room_6.tags.add('lodge#1', category='instance')

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
