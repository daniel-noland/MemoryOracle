#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import asyncio
import websockets

@asyncio.coroutine
def hello(websocket, path):
    while True:
        if not websocket.open:
            print("websocket closed!")
            break
        yield from websocket.send("super test")
        yield from websocket.send("super test")
        name = yield from websocket.recv()
        if name is None:
            print("Name is none!")
            break
        print("< {}".format(name))
        greeting = "Hello {}!".format(name)
        yield from websocket.send(greeting)
        print("> {}".format(greeting))

start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

print("After server!")
