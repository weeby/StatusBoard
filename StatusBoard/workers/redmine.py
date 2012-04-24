# -*- coding: utf-8 -*-
"""Redmine integration worker."""

import StatusBoard.worker
import tornado.httpclient
import json
from copy import deepcopy, copy
import logging
import datetime

class RedmineWorker(StatusBoard.worker.ScheduledWorker):
    """Redmine integration worker."""
    timeout = 300
    
    _endpoints = {
        'users': '/users.json',
        'time_entries': '/time_entries.json?limit=100',
        'issues': '/issues.json?project_id=%d&tracker_id=%d&status_id=%s&limit=1',
        'project': '/projects/%d.json'
    }
    
    def _redmine_api_request(self, endpoint):
        """Return a HTTPRequest for an API endpoint."""
        api_base = self._application.settings['redmine']['api_base']
        if api_base.endswith('/') == False:
            api_base += '/'
            
        if endpoint.startswith('/') == True:
            endpoint = endpoint[1:]
        
        return tornado.httpclient.HTTPRequest(
            api_base + endpoint,
            headers={ 'X-Redmine-API-Key': self._application.settings['redmine']['api_key'] }
        )
    
    def warmup(self):
        logging.info('RedmineWorker: Warming up.')
        self._projects = dict()
        self._new_projects = dict()
        self._users = dict()
        self._queue = list()
        self._client_mode = False
        
        self._issues = dict()
        for tracker_id in self._application.settings['redmine']['issue_trackers'].keys():
            self._issues[tracker_id] = { 'open': 0, 'closed': 0 }
        
        http_client = tornado.httpclient.HTTPClient()
        
        users_req = self._redmine_api_request(self._endpoints['users'])
        users_rsp = http_client.fetch(users_req)
        self._read_users(users_rsp)
        
        time_entries_req = self._redmine_api_request(self._endpoints['time_entries'])
        time_entries_rsp = http_client.fetch(time_entries_req)
        self._read_time_entries(time_entries_rsp)
        
        for project_id in self._new_projects.keys():
            for tracker_id in self._application.settings['redmine']['issue_trackers'].keys():
                open_issues_req = self._redmine_api_request(
                    self._endpoints['issues'] % (project_id, tracker_id, 'open')
                )
                
                response = http_client.fetch(open_issues_req)
                response.rethrow()
                
                data = json.loads(response.body)
                self._new_projects[project_id]['issues'][tracker_id]['open'] = data['total_count']
                
                closed_issues_req = self._redmine_api_request(
                    self._endpoints['issues'] % (project_id, tracker_id, 'closed')
                )
                
                response = http_client.fetch(closed_issues_req)
                response.rethrow()
                
                data = json.loads(response.body)
                
                self._new_projects[project_id]['issues'][tracker_id]['closed'] = data['total_count']
                
        self._projects = copy(self._new_projects)
        self._new_projects = dict()
                
        logging.info('RedmineWorker: Warmed up.')
        
    def status(self):
        response = { 'projects': [] }
        
        for project_id in self._projects:
            project = copy(self._projects[project_id])
            project['id'] = project_id
            response['projects'].append(project)
        
        return response
    
    def _read_users(self, response):
        """Read Redmine users list and extract app-specific data."""
        response.rethrow()
        
        data = json.loads(response.body)
        
        for user in data['users']:
            self._users[user['id']] = user['mail']
    
    def _read_time_entries(self, response):
        """Read Redmine time entries list and extract app-specific data."""
        response.rethrow()
        
        data = json.loads(response.body)
            
        today = datetime.date.today()
        
        self._new_projects = dict()
        
        for entry in data['time_entries']:
            entry_created_on = entry['created_on'].split(' ')[0].split('/')
            entry_date = datetime.date(int(entry_created_on[0]), int(entry_created_on[1]), int(entry_created_on[2]))
            delta = today - entry_date
            
            if delta.days <= 5:
                if self._new_projects.has_key(entry['project']['id']) == False:
                    self._new_projects[entry['project']['id']] = {
                        'name': entry['project']['name'],
                        'people': list(),
                        'issues': deepcopy(self._issues)
                    }
                
                person_id = self._person_idx('redmine_mail', self._users[entry['user']['id']])
                if person_id != None:
                    try:
                        self._new_projects[entry['project']['id']]['people'].index(person_id)
                    except:
                        self._new_projects[entry['project']['id']]['people'].append(person_id)
            else:
                logging.debug('Skipping time entry %d.' % (entry['id'], ))
                
    def _queue_done(self):
        """Emit new projects info to our listeners."""
        logging.debug('Queue done. Kthxbye.')
        self._projects = copy(self._new_projects)
        self._application.emit('redmine', self.status())
        self.start()
    
    def _on_fetch_issues(self, job, response):
        """Handle newly fetched issues list for a job."""
        response.rethrow()
        
        data = json.loads(response.body)
        
        self._new_projects[job[0]]['issues'][job[1]][job[2]] = data['total_count']
        
        self._next_job()
                
    def _next_job(self):
        """Execute next pending request from the queue or finish the job."""
        try:
            job = self._queue.pop()
        except:
            self._queue_done()
        else:
            logging.debug('Got job. project_id = %d, tracker_id = %d, status_id = %s' % job)
            http_client = tornado.httpclient.AsyncHTTPClient()
            req = self._redmine_api_request(
                self._endpoints['issues'] %  job
            )
            
            http_client.fetch(req, lambda rsp: self._on_fetch_issues(job, rsp))
            
    def _on_fetch_time_entries(self, response):
        """Handle newly fetched time entries list."""
        self._read_time_entries(response)
        
        self._queue = list()
        for project_id in self._new_projects.keys():
            for tracker_id in self._application.settings['redmine']['issue_trackers'].keys():
                for status_id in ( 'open', 'closed' ):
                    self._queue.append((
                        project_id, tracker_id, status_id
                    ))
                    
        self._queue.reverse()
                    
        self._next_job()
                
    def _on_timeout(self):
        logging.info('RedmineWorker: Timelimit hit.')
        
        self.stop()
        if self._client_mode == True:
            logging.info('RedmineWorker: Client mode is on.')
            self._queue_done()
        else:
            http_client = tornado.httpclient.AsyncHTTPClient()
            time_entries_req = self._redmine_api_request(self._endpoints['time_entries'])
            
            http_client.fetch(time_entries_req, self._on_fetch_time_entries)
        
    def client_mode(self, mode, projects=None):
        """Client mode handler.
        
        The idea is that when `on` it hacks Redmine status so that it displays
        all present people as if they were working on given projects.
        
        Cheating is bad, we know, but it's also fun :)."""
        if mode == 'on':
            self.stop()
            logging.info('Enabling client mode for projects [ %s ].' % (', '.join(projects), ))
            active_hosts = self._application.workers['pinger'].active_hosts()
            
            people = []
            for person_idx in range(len(self._application.settings['people'])):
                if self._application.settings['people'][person_idx]['ip'] in active_hosts:
                    people.append(str(person_idx))
            
            self._new_projects = dict()
            
            http_client = tornado.httpclient.HTTPClient() # Blocking, mind you.
            for project_id in projects:
                project_id = int(project_id)
                
                if self._projects.has_key(project_id):
                    self._new_projects[project_id] = copy(self._projects[project_id])
                else:
                    project_req = self._redmine_api_request(
                        self._endpoints['project'] % (project_id, )
                    )
                    response = http_client.fetch(project_req)
                    response.rethrow()
                    
                    data = json.loads(response.body)
                    
                    self._new_projects[project_id] = {
                        'name': data['project']['name'],
                        'issues': deepcopy(self._issues),
                        'people': list()
                    }
                    
                    for tracker_id in self._application.settings['redmine']['issue_trackers'].keys():
                        open_issues_req = self._redmine_api_request(
                            self._endpoints['issues'] % (project_id, tracker_id, 'open')
                        )
                        
                        response = http_client.fetch(open_issues_req)
                        response.rethrow()
                        
                        data = json.loads(response.body)
                        self._new_projects[project_id]['issues'][tracker_id]['open'] = data['total_count']
                        
                        closed_issues_req = self._redmine_api_request(
                            self._endpoints['issues'] % (project_id, tracker_id, 'closed')
                        )
                        
                        response = http_client.fetch(closed_issues_req)
                        response.rethrow()
                        
                        data = json.loads(response.body)
                        
                        self._new_projects[project_id]['issues'][tracker_id]['closed'] = data['total_count']
                        
                self._new_projects[project_id]['people'] = people
            
            for project_id in self._projects:
                if str(project_id) not in projects:
                    self._new_projects[project_id] = copy(self._projects[project_id])
                    self._new_projects[project_id]['people'] = []
                    
                if len(self._new_projects) == 5:
                    break
                    
            self._client_mode = True
            self._on_timeout()
        elif mode == 'off':
            self.stop()
            logging.info('Disabling client mode for projects.')
            self._client_mode = False
            self._on_timeout()
        else:
            pass