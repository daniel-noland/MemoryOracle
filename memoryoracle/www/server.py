#!/usr/bin/env python
# -*- encoding UTF-8 -*-
import http
import http.server
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
