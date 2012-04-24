#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path = [ '' ] + sys.path

from optparse import OptionParser
from StatusBoard.app import create_app
import tornado.ioloop
import config

def main():
    parser = OptionParser()
    parser.set_usage('%prog [options]')
    parser.add_option('-a', '--address', dest="address", help="address to bind to. Defaults to 127.0.0.1", action="store", default="127.0.0.1")
    parser.add_option('-p', '--port', dest="port", help="port to bind to. Defaults to 9001.", action="store", type="int", default=9001)
    parser.add_option('-d', '--debug', dest="debug", help="debugging", action="store_true", default=False)
    options, args = parser.parse_args()
    
    config.app_config['debug'] = options.debug
    config.app_config['socket_io_port'] = options.port
    
    application = create_app(config.channels, config.app_config)
    application.start_workers()
    
    application.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ in ('main', '__main__'):    
    main()