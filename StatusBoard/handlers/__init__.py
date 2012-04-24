# -*- coding: utf-8 -*-
"""Request handlers."""

import tornado.web
import json
from StatusBoard.toolkit import SetEncoder
from hashlib import md5
import sqlite3

class IndexHandler(tornado.web.RequestHandler):
    """Handler for root URL."""
    
    def get(self):
        """Renders index template used to bootstrap the app."""
        self.render('../templates/index.html')
        
class StatusHandler(tornado.web.RequestHandler):
    """Handler for getting worker status."""
    
    def get(self, channel_name):
        """Returns status of a specified worker."""
        try:
            status = self.application.workers[channel_name].status()
        except KeyError:
            is_json = True
            status = json.dumps(None)
        else:
            is_json = False
            if isinstance(status, dict):
                is_json = True
                status = json.dumps(status, cls=SetEncoder)
            
        if is_json == True:
            self.set_header('Content-Type', 'application/json; charset=utf-8')
        
        self.write(status)
            
    def post(self, channel_name):
        """Forces a worker identified by ``channel_name`` to refresh as if its
        timelimit was hit."""
        self.application.workers[channel_name].force_refresh()
        self.write('OK')
            
class PeopleHandler(tornado.web.RequestHandler):
    """Handler for list of people."""
    _h4x0r3d = dict()
    
    def get(self):
        """Returns list of people."""
        response = {}
        
        for i in range(len(self.application.settings['people'])):
            person = self.application.settings['people'][i]
            
            if self._h4x0r3d.has_key(person['gravatar_mail']):
                response[i] = self._h4x0r3d[person['gravatar_mail']]
            else:
                response[i] = {
                    'name': person['name'],
                    'gravatar_hash': md5(person['gravatar_mail'].lower()).hexdigest()
                }
            
        self.write(response)
        
    def post(self):
        """Hacks a person entry in people list.
        
        HOWTO:
        * POST /people body: person_idx=<person_idx>&name=<new_name>&gravatar_hash=<gravatar_hash>
        * Disco! :)"""
        try:
            current_person = self.application.settings['people'][int(self.get_argument('person_idx'))]
        except IndexError:
            raise tornado.web.HTTPError(400)
        
        new_person = {}
        
        try:
            new_person['name'] = self.get_argument('name')
        except:
            new_person['name'] = current_person['name']
        
        try:
            new_person['gravatar_hash'] = self.get_argument('gravatar_hash')
        except:
            new_person['gravatar_hash'] = md5(current_person['gravatar_mail'].lower()).hexdigest()
        
        if len(new_person) == 0:
            raise tornado.web.HTTPError(400)
            
        self.application.emit('sysmsg', 'h4x0r_people')
        self._h4x0r3d[current_person['gravatar_mail']] = new_person
        self.write('Kaboom!')
        
    def delete(self):
        """Unhacks a person entry."""
        try:
            current_person = self.application.settings['people'][int(self.get_argument('person_idx'))]
        except IndexError:
            raise tornado.web.HTTPError(400)
            
        try:
            del(self._h4x0r3d[current_person['gravatar_mail']])
        except:
            raise tornado.web.HTTPError(400)
            
        self.application.emit('sysmsg', 'h4x0r_people')
        self.write('Bummer.')
        
class XMPPBrowserHandler(tornado.web.RequestHandler):
    """Browser for XMPP messages archive."""
    _db = None
    def initialize(self):
        if self._db == None and self.application.settings['xmpp_bot']['database'] != None:
            self._db = sqlite3.connect(self.application.settings['xmpp_bot']['database'])
            
    def get(self):
        if self._db != None:
            cursor = self._db.cursor()
            
            try:
                offset = int(self.get_argument('offset', 0))
            except:
                raise tornado.web.HTTPError(400)
                
            cursor.execute('SELECT * FROM xmpp_messages ORDER BY created_at DESC LIMIT 10 OFFSET %d' % (offset, ))
            response = { 'messages': [] }
            for row in cursor:
                payload = json.loads(row[2])
                
                response['messages'].append({
                    'author': self.application.settings['people'][int(payload['person'])]['name'],
                    'created_at': row[1],
                    'message': payload['message'],
                })
                
            self.write(response)
            
        else:
            raise tornado.web.HTTPError(501)