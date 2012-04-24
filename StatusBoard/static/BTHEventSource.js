/*
 
BTHEventSource
Cross-browser Server-Sent Events Wrapper

Copyright (C) 2011 by Tomasz Wójcik <labs@tomekwojcik.pl>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

*/
(function() {
    var BTHEventSource = function(url, force_xhr) {
        if (force_xhr === undefined) {
            this._force_xhr = false;
        } else {
            this._force_xhr = true;
        }
        
        this._handlers = {};
        this._message_handlers = {};
        this._transport = null;
        this._xhr_virgin = true; // :)
        this._xhr_last_id = null;
        this._use_xhr_last_id = null;
        this._xhr_reconnect_timeout = null;
        this.url = url;
    };
    
    BTHEventSource.prototype.open = function(listener) {
        this._handlers['open'] = listener;
    };
    
    BTHEventSource.prototype.close = function(listener) {
        this._handlers['close'] = listener;
    };
    
    BTHEventSource.prototype.message = function() {
        var shift = Array.prototype.shift;
        
        var arg0 = shift.apply(arguments);
        var arg1 = shift.apply(arguments);
        
        if (typeof(arg0) === 'function') {
            this._handlers['message'] = arg0;
        } else {
            this._message_handlers[arg0] = arg1;
        }
    };
    
    BTHEventSource.prototype.error = function(listener) {
        this._handlers['error'] = listener;
    };
    
    var start_long_polling = function(self) {
        var timeout = null;
        var reconnect_timeout = null;
        var xhr_has_timed_out = false;
        
        var on_xhr_timeout = function() {
            xhr_has_timed_out = true;
            self._transport.abort();
            window.clearTimeout(timeout);
            timeout = null;
            start_long_polling(self);
        };
        
        var on_ready_state_change = function() {
            window.clearTimeout(timeout);
            timeout = null;
            
            var fire_general_event = function(event) {
                event = event || null;
                var handler = undefined;
                
                if (event !== null) {
                    handler = self._handlers[event];
                    if (handler !== undefined) {
                        handler();
                    }
                }
            };
            
            if (self._transport.readyState === 4)
            {
                if (self._transport.status !== 0) {
                    if (self._transport.status === 200) {
                        if (self._transport.responseText !== '') {
                            var data = JSON.parse(self._transport.responseText);
                            var handler = null;
                            
                            if (self._xhr_virgin === true) {
                                fire_general_event('open');
                                self._xhr_virgin = false;
                            }
                            
                            if (data.event === undefined) {
                                handler = self._handlers['message'];
                            } else {
                                handler = self._message_handlers[data.event];
                            }
                            
                            if (data.id !== undefined) {
                                self._xhr_last_id = data.id;
                            }
                            
                            if (handler !== undefined) {
                                handler(data.data);
                            }
                        }
                    } else {
                        fire_general_event('error');
                        self._use_xhr_last_id = true;
                    }
                    start_long_polling(self);
                } else {
                    if (xhr_has_timed_out === true) {
                        fire_general_event('close');
                    } else {
                        fire_general_event('error');
                    }
                    
                    self._use_xhr_last_id = true;
                    self._xhr_reconnect_timeout = window.setTimeout(function() {
                        window.clearTimeout(self._xhr_reconnect_timeout);
                        self._xhr_reconnect_timeout = null;
                        start_long_polling(self);
                    }, 3000);
                }
            }
        };
        
        if (window.XMLHttpRequest !== undefined) {
            self._transport = new XMLHttpRequest();
        } else {
            self._transport = new ActiveXObject('MSXML2.XMLHTTP.3.0');
        }
        self._transport.onreadystatechange = on_ready_state_change;
        
        if (self._use_xhr_last_id == true) {
            self._transport.open('POST', self.url + '?last_event_id=' + self._xhr_last_id);
            self._use_xhr_last_id = false;
        } else {
            self._transport.open('POST', self.url);
        }
        
        timeout = window.setTimeout(on_xhr_timeout, 15000);
        self._transport.send();
    };
    
    BTHEventSource.prototype.start = function() {
        if ((this._force_xhr == true) || (typeof(window.EventSource) === 'undefined')) {
            start_long_polling(this);
        } else {
            var self = this;
            var url = self.url;
            var item = null;
            if (window.opera !== undefined) {
                if (url.indexOf('?') !== -1) {
                    url += '&opera=1';
                } else {
                    url += '?opera=1';
                }
            }
            this._transport = new EventSource(this.url);
            this._transport.onerror = function(event) {
                var handler = undefined;
                if (event.eventPhase == EventSource.CLOSED) {
                    handler = self._handlers.close;
                } else {
                    handler = self._handlers.error;
                }
                
                if (handler !== undefined) {
                    handler();
                }
            };
            this._transport.onopen = this._handlers.open || function() {};
            var self = this;
            this._transport.onmessage = function(data) {
                var handler = self._handlers.message;
                if (handler !== undefined) {
                    handler(JSON.parse(data.data));
                }
            };
            
            for(item in this._message_handlers) {
                if (this._message_handlers.hasOwnProperty(item) === true) {
                    this._transport.addEventListener(item, function(data) {
                        var handler = self._message_handlers[data.type];
                        handler(JSON.parse(data.data));
                    }, false);
                }
            }
        }
    };
    
    BTHEventSource.prototype.stop = function() {
        if (typeof(this._transport.abort) === 'function') {
            this._transport.abort();
        } else {
            this._transport.close();
        }
    };
    
    window.BTHEventSource = BTHEventSource;
})();