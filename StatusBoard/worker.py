# -*- coding: utf-8 -*-
"""Abstract classes for workers."""

import tornado.ioloop
import time

class BaseWorker(object):
    """Base worker class. Subclass it to create other worker classes."""
    
    def __init__(self, application, **kwargs):
        """Constructor."""
        self._application = application
        self._options = kwargs
        self.warmup()
            
    def _person_idx(self, key, value, default_key='gravatar_mail'):
        """Filters people list and returns index of entry that matches search
        criteria."""
        for i in range(len(self._application.settings['people'])):
            person = self._application.settings['people'][i]
            test_value = person.get(key, None)
            if test_value == None:
                test_value = person[default_key]
                
            if test_value == value:
                return str(i)
            
        return None
        
    def warmup(self):
        """Warmup the worker, if needed. This will be invoked when application
        is launched to initialize data for workers so that when the first client
        connects there is something to send them. This method should block the
        calling thread.
        
        Default implementation does nothing."""
        pass
    
    def status(self):
        """Status of the worker. This should be used to initialize new clients
        with current worker data."""
        raise NotImplementedError
    
    def start(self):
        """Start the worker."""
        raise NotImplementedError
    
    def stop(self):
        """Stop the worker."""
        raise NotImplementedError
    
    def force_refresh(self):
        """Force refresh of the worker."""
        raise NotImplementedError
    
class PeriodicWorker(BaseWorker):
    """Periodic worker base class.
    
    Periodic workers use tornado.ioloop.PeriodicCallback instances to schedule
    their execution at a given interval."""
    
    interval = 5000 # 5 seconds
    
    def __init__(self, *args, **kwargs):
        self._periodic_callback = None
        
        BaseWorker.__init__(self, *args, **kwargs)
        
    def start(self):
        if self._periodic_callback == None:
            self._periodic_callback = tornado.ioloop.PeriodicCallback(
                self._on_periodic_callback, self.interval
            )
            
        self._periodic_callback.start()
        
    def stop(self):
        self._periodic_callback.stop()
        
    def force_refresh(self):
        self.stop()
        self._on_periodic_callback()
        self.start()
            
    def _on_periodic_callback(self):
        """Callback fired by Tornado IOLoop when timelimit is hit."""
        raise NotImplementedError
    
class ScheduledWorker(BaseWorker):
    """Scheduled worker base class.
    
    Scheduled workers use tornado.IOLoop.add_timeout to schedule their execution
    after a given timeout. The worker will execute only once and in order to be
    executed again it has to be scheduled manually."""
    
    timeout = 5 # 5 seconds
    
    def __init__(self, *args, **kwargs):
        self._timeout = None
        
        BaseWorker.__init__(self, *args, **kwargs)
        
    def start(self):
        if self._timeout == None:
            self._timeout = tornado.ioloop.IOLoop.instance().add_timeout(
                time.time() + self.timeout, self._on_timeout
            )
            
    def stop(self):
        try:
            tornado.ioloop.IOLoop.instance().remove_timeout(self._timeout)
        except:
            pass
        
        self._timeout = None
        
    def force_refresh(self):
        self.stop()
        self._on_timeout()
        
    def _on_timeout(self):
        """Callback fired by Tornado IOLoop when timelimit is hit."""
        raise NotImplementedError