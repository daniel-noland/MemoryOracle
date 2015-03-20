#!/usr/bin/env python
# -*- encoding UTF-8 -*-

import asyncio
import websockets

@asyncio.coroutine
def hello():
    while True:
        websocket = yield from websockets.connect('ws://localhost:8765/')
        name = input("What's your name? ")
        if not websocket.open:
            print("Websocket closed!")
            break
        yield from websocket.send(name)
        print("> {}".format(name))
        greeting = yield from websocket.recv()
        if greeting is None:
            print("greeting is None!")
            break
        print("< {}".format(greeting))

asyncio.get_event_loop().run_until_complete(hello())
