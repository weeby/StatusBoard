# -*- coding: utf-8 -*-
"""Pinger worker."""

import tornado.ioloop
import StatusBoard.worker
import subprocess
import time
import shlex
import logging

class PingerWorker(StatusBoard.worker.ScheduledWorker):
    timeout = 60
    cmd = 'ping -t 2 -c 1 %s'
    
    def _start_ping(self, ip):
        """Starts pinging a host and returns the subprocess object."""
        command = shlex.split(self.cmd % (ip, ))
        
        logging.debug('PingerWorker: Pinging %s' % (ip, ))
        return subprocess.Popen(command, stdout=self._dev_null, stderr=self._dev_null)
        
    def warmup(self):
        logging.info('PingerWorker: Warming up.')
        self._active_hosts = set()
        self._inactive_hosts = set()
        self._dev_null = open('/dev/null', 'wb')
        
        for person in self._application.settings['people']:
            try:
                process = self._start_ping(person['ip'])
            except KeyError:
                continue
            
            return_code = process.wait()
            if return_code == 0:
                self._active_hosts.add(person['ip'])
            else:
                self._inactive_hosts.add(person['ip'])
        
        logging.info('PingerWorker: Warmed up.')
        
    def status(self):
        return { 'active': len(self._active_hosts), 'inactive': len(self._inactive_hosts) }
                
    def _ping(self):
        """Starts async pinging queue."""
        try:
            person = self._application.settings['people'][self._current_idx]
        except IndexError:
            self._application.emit('pinger', self.status())
            self.stop()
            self.start()
        else:
            try:
                self._current_ip = person['ip']
            except KeyError:
                self._current_idx += 1
                self._ping()
                return
            
            self._process = self._start_ping(self._current_ip)
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 1, self._waiter)
    
    def _waiter(self):
        """Waits for the child process to finish and interprets the result."""
        return_code = self._process.poll()
        
        if return_code == None:
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 1, self._waiter)
        else:
            if return_code == 0:
                self._active_hosts.add(self._current_ip)
                
                try:
                    self._inactive_hosts.remove(self._current_ip)
                except:
                    pass
            else:
                self._inactive_hosts.add(self._current_ip)
                
                try:
                    self._active_hosts.remove(self._current_ip)
                except:
                    pass
                    
            self._process = None
            self._current_idx += 1
            self._ping()
        
    def _on_timeout(self):
        logging.info('PingerWorker: Timelimit hit.')
        self._current_idx = 0
        self._ping()
        
    def active_hosts(self):
        """Getter for self._active_hosts."""
        return self._active_hosts
    
    def inactive_hosts(self):
        """Getter for self._inactive_hosts."""
        return self._inactive_hosts