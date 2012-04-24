# -*- coding: utf-8 -*-
"""Application class."""

import logging
import tornado.web
import tornado.httpclient
#import tornadio
import StatusBoard.handlers
#import StatusBoard.channel
import os.path
import btheventsource

class StatusBoardApplication(tornado.web.Application):
    """Custom tornado.web.Application subclass."""
    
    channels = set()
    workers = dict()
    
    @classmethod
    def add_listener(self, channel_name, channel_listener):
        """Registers a listener for the channel."""    
        self.channels.add(channel_listener)
        
    @classmethod
    def remove_listener(self, channel_name, channel_listener):
        """Registers a listener from the channel."""
        self.channels.remove(channel_listener)
        
    @classmethod
    def register_worker(self, channel_name, worker):
        """Registers a worker for a channel."""
        self.workers[channel_name] = worker
        
    @classmethod
    def remove_worker(self, channel_name):
        """Removes a worker for a channel."""
        del(self.workers[channel_name])
        
    def start_workers(self):
        """Starts registered workers."""
        for channel_name in self.workers:
            self.workers[channel_name].start()
    
    def emit(self, channel_name, message):
        """Emit the message to channel listeners."""
        logging.debug('Emitting event "%s": %s', channel_name, message)
        for listener in self.channels:
            try:
                listener.emit(message, channel_name)
            except IOError:
                # The stream is closed but the listener hasn't been removed.
                pass
            except AssertionError:
                # The response is finished.
                pass
            except RuntimeError:
                # ARRRR! :D
                pass
        
class Channel(btheventsource.BTHEventStreamHandler):
    @tornado.web.asynchronous
    def get(self):
        StatusBoardApplication.add_listener('events', self)
        
    @tornado.web.asynchronous
    def post(self):
        StatusBoardApplication.add_listener('events', self)
            
# Routing table.
default_routes = [
    (r'/', StatusBoard.handlers.IndexHandler),
    (r'/people', StatusBoard.handlers.PeopleHandler),
    (r'/status/(.+?)', StatusBoard.handlers.StatusHandler),
    (r'/xmpp/browse', StatusBoard.handlers.XMPPBrowserHandler),
    (r'/events', Channel)
]
            
def create_app(channels=None, config=None):
    """Instantiates and initializes the app according to config dict."""
    if channels == None or len(channels) == 0:
        raise RuntimeError('No channels defined.')
    
    if config == None:
        raise RuntimeError('No configuration given.')
        
    config['static_path'] = os.path.join(os.path.dirname(__file__), 'static')
    
    logging_config = {
        'format': "%(asctime)s %(name)s <%(levelname)s>: %(message)s",
        'level': logging.INFO
    }
    
    if config.get('debug', False):
        logging_config['level'] = logging.DEBUG
        
    logging.basicConfig(**logging_config)
    
    try:
        default_routes.append(
            (r'/(logo\.png)', tornado.web.StaticFileHandler, { 'path': config['logos_path'] }),
        )
        default_routes.append(
            (r'/(blanker_logo\.png)', tornado.web.StaticFileHandler, { 'path': config['logos_path'] }),
        )
    except KeyError:
        pass
        
    app = StatusBoardApplication(default_routes, **config)
    
    for channel_name in channels:
        worker_cls = channels[channel_name]
        worker = worker_cls(app)
        app.register_worker(channel_name, worker)
    
    return app