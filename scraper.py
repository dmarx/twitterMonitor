from __future__ import division
from connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from twython import TwythonStreamer
from requests.exceptions import ChunkedEncodingError
import time
from datamodel import DbApi

db = DbApi()
tweet = None
class MyStreamer(TwythonStreamer):
    
    def on_success(self, data):
        global tweet
        tweet = data
        self.backoff = 1
        if 'text' not in data: # more general. handles all notices 
            return
        if any(k in data['entities'].keys() for k in ('urls', 'media')):
            db.persist(data)
            #try:
            #    print data['text']
            #except:
            #    print "unicode issue"
    def on_error(self, status_code, data):
        if not hasattr(self, 'backoff'):
            self.backoff = 1
        print "[ON ERROR]", status_code
        if status_code == 420:
            print "Sleeping", self.backoff
            time.sleep(self.backoff)
            self.backoff *= 2 # Exponential backoff
            if self.backoff > 15*60: # Don't sleep longer than 15 minutes
                self.backoff = 15*60
            
if __name__ == "__main__":
    from collections import Counter
    from load_terms import load_terms
    
    exception_catcher = Counter()
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    
    terms = load_terms()
    
    while True:
        #stream.statuses.filter(track=terms)
        #"""
        try:
            stream.statuses.filter(track=terms)
            #stream.statuses.filter(track=['hillary', 'trump', 'election'])
        except ChunkedEncodingError, e:
            exception_catcher[e] +=1
            print "[SCRAPER ERROR]", e, exception_catcher[e]
        except Exception, e:        
            exception_catcher[e] +=1
            print "[SCRAPER ERROR]", e, exception_catcher[e]
            db.conn.close()
            raise e
        
        #"""