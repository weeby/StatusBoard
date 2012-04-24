# -*- coding: utf-8 -*-
"""Yahoo! Weather integration worker."""

import StatusBoard.worker
import tornado.httpclient
import xml.parsers.expat
import logging
import re
import datetime

class YahooWeatherRSSParser(object):
    """Parse Yahoo! Weather RSS feed to extract info from it.
    
    XML API responses are so '90s."""
    
    def __init__(self):
        """Constructor."""
        self._is_description_block = False
        self._description = u''
        self._response = dict()
        self._re_description_img = re.compile(r'img src="(.+?)"', re.M)
        
    def _on_start_element(self, element, attrs):
        """Element start handler."""
        # Sooooooo lame.
        if element == 'yweather:location':
            self._response['city'] = attrs['city']
            self._response['country'] = attrs['country']
        elif element == 'yweather:condition':
            self._response['temperature'] = attrs['temp']
            self._response['description'] = attrs['text'] # TODO: I18N
            
            code = 'na'
            if int(attrs['code']) <= 47:
                code = attrs['code']
                
            self._response['icon_code'] = code
        elif element == 'yweather:units':
            self._response['temperature_unit'] = attrs['temperature']
    
    def _on_cdata(self, data):
        """Character data handler."""
        if self._is_description_block == True:
            self._description += data
    
    def _on_start_cdata_section(self):
        """CDATA section start handler."""
        self._is_description_block = True
        
    def _on_end_cdata_section(self):
        """CDATA section end handler. Extracts image URL from description."""
        self._is_description_block = False
        
        match = self._re_description_img.search(self._description)
        if match != None:
            try:
                self._response['img'] = match.group(1)
            except:
                pass
    
    def parse(self, xml_data):
        """Parse `xml_data` and return result."""
        parser = xml.parsers.expat.ParserCreate('utf-8')
        parser.StartElementHandler = self._on_start_element
        
        parser.Parse(xml_data, True)
        
        return self._response

class YahooWeatherWorker(StatusBoard.worker.PeriodicWorker):
    """Yahoo! Weather integration worker."""
    interval = 3600000 # 1 hour
    
    def _yahoo_weather_request(self):
        """Return a HTTPRequest for forecast."""
        return tornado.httpclient.HTTPRequest(
            'http://weather.yahooapis.com/forecastrss?w=%s&u=%s' % (
                self._application.settings['yahoo_weather']['woeid'],
                self._application.settings['yahoo_weather']['unit']
            )
        )
        
    def _read_forecast(self, xml):
        parser = YahooWeatherRSSParser()
        return parser.parse(xml)
    
    def _on_fetch_forecast(self, response):
        """Read weather forecast RSS."""
        response.rethrow()
        self._status = self._read_forecast(response.body)
        self._application.emit('weather', self._status)
    
    def warmup(self):
        logging.info('YahooWeatherWorker: Warming up.')
        self._status = dict()
        http_client = tornado.httpclient.HTTPClient()
        
        req = self._yahoo_weather_request()
        response = http_client.fetch(req)
        self._status = self._read_forecast(response.body)
        
        logging.info('YahooWeatherWorker: Warmed up.')
        
    def status(self):
        return self._status
    
    def _on_periodic_callback(self):
        logging.info('YahooWeatherWorker: Timelimit hit.')
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        req = self._yahoo_weather_request()
        http_client.fetch(req, self._on_fetch_forecast)