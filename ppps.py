#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 websocket server of pub/sub pattern
 Usage:
   [PORT=<port>] python -m ppps
"""
import gevent.monkey as _; _.patch_all()
import os, sys, traceback
from geventwebsocket import WebSocketServer
no_cache = 'no-cache, no-store, must-revalidate'
def headers(typ):
    return [('Content-Type', typ),
            ('Access-Control-Allow-Origin', '*'),
            ('Cache-Control', no_cache),
            ('Pragma', 'no-cache'),
            ('Expires', '0')]
Channels = {}
def pub(chn, msg, user = None, ttl=3):
    if ttl > 9:
        print("ttl overflow")
        return
    if ttl > 0:
        for u in Channels.get(chn, []):
            if u != user:
                u.send('%s;%s;%s' % (ttl, chn, msg))
def sub(chn, user):
    Channels[chn] = Channels.get(chn, []) + [user]
def uns(chn, user):
    return Channels.get(chn, []).remove(user)
def uns_all(user):
    [ uns(k, user) for k,v in Channels.items() ]
def app(env, start):
    ws = env.get("wsgi.websocket", None)
    if not ws:
        start('400 NOPE', headers('text/plain'))
        yield b'No way!!\n'
        return
    try:
        print("HANDLE WS", ws)
        myid = 'I%x' % id(ws)
        sub(myid, ws)
        pub(myid, "hello there")
        msg = ws.receive()
        while msg:
            print("MSG1", repr(msg))
            m0, m1, m2 = msg.split(';', 2)
            print("MSG2", repr((m0, m1, m2)))
            if   m1 == '+': sub(m2, ws)
            elif m1 == '-': uns(m2, ws)
            else:           pub(m1, m2, ws, int(m0)-1)
            msg = ws.receive()
    except:
        print('='*20)
        traceback.print_exc()
        print('='*20)
    finally:
        uns_all(ws)
if __name__=='__main__':
    port = int(os.getenv('PORT', 8090))
    WebSocketServer(('', port), app).serve_forever()
