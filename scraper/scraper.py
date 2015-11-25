from __future__ import division
from connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from utilities import store_tweets, handle_rate_limiting
from twython import TwythonStreamer
from requests.exceptions import ChunkedEncodingError
from cache import TweetCache

import time
start = time.time()
update_interval = 60

# Looks like the TwythonStreamer class handles rate limiting for me!
tweet = None
tweet_cache = TweetCache(minutes=60)

#tweet_cache=[]
N=0
M=0
class MyStreamer(TwythonStreamer):
    def on_success(self, data):
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
                print "{:.2f} | {:.2f} | {}".format(score, score, item)
                
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
                print "{:.2f} | {:.2f} | {}".format(score, score, item)
                
            start = time.time()
            
            #raise Exception("FOOBAARRRR!!!")
            
    def on_error(self, status_code, data):
        print "[ON ERROR]", status_code

if __name__ == "__main__":
    from collections import Counter
    exception_catcher = Counter()
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    #tweet_cache.register_datastore(tweets)
    import redis
    r = redis.StrictRedis()
    tweet_cache.register_pubsub(r, 'tweet_monitor')
    while True:
        try:
            stream.statuses.filter(track=
                ['terrorist','terrorists','attack','attacked','killed',
                'hostage','hostages','explosion','bomb','bomber','gunman',
                'gunmen','breaking','war','dead','injured','emergency', 
                'casualties','kidnapped','mob','protest','protesters',
                'shooting','gunfire','arrested','alleged','suspect','suspects',
                'suspected'])
            #stream.statuses.sample()
        except Exception, e:
            exception_catcher[e] +=1
            print "[ERROR]", e, exception_catcher[e]
            #raise e
    