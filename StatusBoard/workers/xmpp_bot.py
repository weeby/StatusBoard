# -*- coding: utf-8 -*-
"""XMPP Bot."""

import StatusBoard.worker
import sleekxmpp
from copy import copy
import sqlite3
import json
import datetime
from functools import partial
import tornado.ioloop
from tornado.escape import xhtml_escape
import logging

class XMPPBot(StatusBoard.worker.BaseWorker):
    """XMPP Bot."""
    
    def __init__(self, *args, **kwargs):
        self._xmpp = None
        StatusBoard.worker.BaseWorker.__init__(self, *args, **kwargs)
        
    def warmup(self):
        logging.info('XMPPBot: Warming up.')
        self._messages = list()
        self._db = None
            
        if self._application.settings['xmpp_bot']['database'] != None:
            self._db = sqlite3.connect(self._application.settings['xmpp_bot']['database'])                
            cursor = self._db.cursor()
            
            cursor.execute('SELECT * FROM xmpp_messages ORDER BY id DESC LIMIT 5')
            for row in cursor:
                self._messages.append(json.loads(row[2]))
        
        logging.info('XMPPBot: Warmed up.')
            
    def status(self):
        response = {}
        for i in range(len(self._messages)):
            response[i] = self._messages[i]
            
        return response
        
    def start(self):
        self._xmpp = sleekxmpp.ClientXMPP(
            self._application.settings['xmpp_bot']['jid'],
            self._application.settings['xmpp_bot']['password']
        )
        
        self._xmpp.connect((
            self._application.settings['xmpp_bot']['server'],
            self._application.settings['xmpp_bot']['port']
        ))
        
        self._xmpp.add_event_handler("session_start", self._on_xmpp_session_start)
        self._xmpp.add_event_handler("message", self._on_xmpp_message)
        
        self._xmpp.process()
        
    def _handle_client_mode(self, msg, *args):
        if len(args) == 0:
            msg.reply('client_mode: mode project,project').send()
            return
        
        mode = args[0]
        
        projects = None
        try:
            projects = args[1].split(',')
        except:
            pass
        
        if mode == 'on':
            if projects == None:
                msg.reply('client_mode: mode project,project').send()
                return
            
            self._application.workers['redmine'].client_mode('on', projects=projects)
        elif mode == 'off':
            self._application.workers['redmine'].client_mode('off', projects=projects)
        else:
            msg.reply('client_mode: mode not found: ' + mode).send()
        
    def _process_command(self, msg):
        command = msg['body'][1:].split(' ')
        
        handler = getattr(self, '_handle_' + command[0], None)
        if handler == None:
            msg.reply('%s: command not found' % (command[0], )).send()
        else:
            args = []
            if len(command) > 1:
                args = command[1:]
            handler(msg, *args)
        
    def _process_xmpp_message(self, msg):
        """Processes and emits the message.
        
        This method does the actual processing and is called automagically from
        self._on_xmpp_message()."""
        if msg['body'].startswith('/') == True:
            self._process_command(msg)
        else:
            author = str(msg['from']).encode('utf-8').split('/')[0]
            person_idx = self._person_idx('jid', author)
            
            if person_idx != None:
                message = {
                    'person': person_idx,
                    'message': xhtml_escape(msg['body'])
                }
                
                self._messages = [ message ] + self._messages
                if len(self._messages) > 3:
                    self._messages.pop()
                    
                if self._db != None:
                    cursor = self._db.cursor()
                    
                    cursor.execute('INSERT INTO xmpp_messages (created_at, payload) VALUES (?, ?)',
                        ( datetime.datetime.now(), json.dumps(message) )
                    )
                    self._db.commit()
                
                self._application.emit('xmpp', message)

    def _on_xmpp_session_start(self, event):
        """Handles XMPP session start event."""
        self._xmpp.send_presence()
        self._xmpp.get_roster()

    def _on_xmpp_message(self, msg):
        """Handles XMPP message event."""
        if msg['type'] in ('chat', 'normal'):
            tornado.ioloop.IOLoop.instance().add_callback(partial(self._process_xmpp_message, msg))