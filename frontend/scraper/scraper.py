from __future__ import division
from connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from utilities import store_tweets, handle_rate_limiting
#from twython import TwythonStreamer
from tweepy import StreamListener
from requests.exceptions import ChunkedEncodingError
from cache import TweetCache
import time
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('../config/connection.cfg')

# spin up twitter api
APP_KEY    = config.get('credentials','app_key')
APP_SECRET = config.get('credentials','app_secret')
OAUTH_TOKEN  = config.get('credentials','oath_token')
OAUTH_TOKEN_SECRET = config.get('credentials','oath_token_secret')


start = time.time()
update_interval = 60

# Looks like the TwythonStreamer class handles rate limiting for me!
tweet = None
tweet_cache = TweetCache(minutes=60)

#tweet_cache=[]
N=0
M=0

class MyStreamer(StreamListener):
    def on_status(self, data):
        self.backoff = 1
        if 'text' not in data: # more general. handles all notices 
            return
        global tweet_cache
        global tweet
        tweet = data
        tweet_cache.update(data)
        global N
        N+=1
        ### every minute, print updated "trends" ###
        global update_interval
        global start
        if time.time() - start > update_interval:
            print "\n\n[UPDATE]", N, len(tweet_cache)
            total_urls  = sum(tweet_cache.urls.values())
            total_media = sum(tweet_cache.media.values())
            print "[URLs] By count"
            for i, item_count in enumerate(tweet_cache.urls.most_common(10)):
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
            print "[URLs] By user"
            for i, item_count in enumerate(tweet_cache.url_users.most_common(10)): 
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
            print "[URLs] By score"
            for i, item_score in enumerate(tweet_cache.url_scores.most_common(10)): 
                item, score = item_score
                count = tweet_cache.urls[item]
                print "{:.4f} | {:.4f} | {}".format(count, score, item)
                
            print "\n[MEDIA] By count"
            for i, item_count in enumerate(tweet_cache.media.most_common(10)):
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
            print "[MEDIA] By user"
            for i, item_count in enumerate(tweet_cache.media_users.most_common(10)): 
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
            print "[MEDIA] By score"
            for i, item_score in enumerate(tweet_cache.media_scores.most_common(10)): 
                item, score = item_score
                count = tweet_cache.media[item]
                print "{:.4f} | {:.4f} | {}".format(count, score, item)
                
            start = time.time()
            
            #raise Exception("FOOBAARRRR!!!")
            
    def on_error(self, status_code):
        if not hasattr(self, 'backoff'):
            self.backoff = 1
        print "[ON ERROR]", status_code
        if status_code == 420:
            #raise Exception
            print "Sleeping", self.backoff
            time.sleep(self.backoff)
            self.backoff *= 2 # Exponential backoff
            if self.backoff > 15*60: # Don't sleep longer than 15 minutes
                self.backoff = 15*60
            
if __name__ == "__main__":
    from collections import Counter
    exception_catcher = Counter()
    auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET)
    auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    api = tweepy.API(auth)
    Listener = MyStreamer()
    stream = tweepy.Stream(auth=api.auth, listener=Listener())
    #stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    #tweet_cache.register_datastore(tweets)
    #import redis
    #r = redis.StrictRedis()
    #tweet_cache.register_pubsub(r, 'tweet_monitor')
    while True:
        try:
            stream.filter(track=
            #stream.statuses.filter(track=
                ['terrorist','terrorists','attack','attacked','attacks','killed',
                'hostage','hostages','explosion','bomb','bomber','gunman',
                'gunmen','breaking','war','dead','injured','emergency', 
                'casualties','kidnapped','mob','protest','protesters',
                'shooting','gunfire','arrested','alleged','suspect','suspects',
                'suspected','assassinate','assassinated'])
            #stream.statuses.sample()
        except ChunkedEncodingError, e:
            exception_catcher[e] +=1
            print "[SCRAPER ERROR]", e, exception_catcher[e]
        except Exception, e:        
            exception_catcher[e] +=1
            print "[SCRAPER ERROR]", e, exception_catcher[e]
            #raise e
    