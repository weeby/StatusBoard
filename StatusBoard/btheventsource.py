# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 by Tomasz Wójcik <labs@tomekwojcik.pl>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Tornado handler for BTHEventSource"""

import tornado.web

try:
    import json
except ImportError:
    import simplejson as json

class BTHEventStreamHandler(tornado.web.RequestHandler):
    def initialize(self):
        accept = self.request.headers.get('Accept', None)
        requested_with = self.request.headers.get('X-Requested-With', None)
        
        self.is_xhr_polling = False
        sse_content_type = 'text/event-stream'
        opera_argument = self.get_argument('opera', None)
        if opera_argument != None:
            sse_content_type = 'application/x-dom-event-stream' # Web standards my ass.
        else:
            if accept != 'text/event-stream' or requested_with == 'XMLHttpRequest':
                self.is_xhr_polling = True
            
        if self.is_xhr_polling == False:
            self.set_header('Content-Type', sse_content_type)
            self.set_header('Cache-Control', 'no-cache')
            self.last_event_id = self.request.headers.get('Last-Event-Id', None)
        else:
            self.last_event_id = self.get_argument('last_event_id', None)
            
    def emit(self, data, event=None, id=None):
        if self.is_xhr_polling == False:
            _data = json.dumps(data)
            _response = u''
            
            if id != None:
                _response += u'id: ' + unicode(id).strip() + u'\n'
            
            if event != None:
                _response += u'event: ' + unicode(event).strip() + u'\n'
                
            _response += u'data: ' + _data.strip() + u'\n\n'
            
            self.write(_response)
            self.flush()
        else:
            _response = { 'data': data }
            
            if event != None:
                _response['event'] = event
            
            if id != None:
                _response['id'] = id
                
            self.write(_response)
            self.finish()