Authentication - guest login and register

Commands - parse inputs 

Rooms - dict of rooms (key: room_id, value: room object)

Broadcasts - shout (all), tell (one), say (room)

Utilities - whos onlines, status/info of user, block/unblock 

Edge Cases - multiple rooms per users, leader leaves -> close room, block users, filter messages

Robustness - never crashes, graceful disconnecting client