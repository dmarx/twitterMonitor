from __future__ import division
from code.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from code.utilities import store_tweets, handle_rate_limiting
from twython import TwythonStreamer
from requests.exceptions import ChunkedEncodingError
from cache import TweetCache

import time
start = 0
update_interval = 60

# Looks like the TwythonStreamer class handles rate limiting for me!
tweet = None
tweet_cache = TweetCache(minutes=60)

#tweet_cache=[]
N=0
M=0
class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        #if 'limit' in data:
        #    return
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
                
            print "\n[MEDIA] By count"
            for i, item_count in enumerate(tweet_cache.media.most_common(10)):
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
            print "[MEDIA] By user"
            for i, item_count in enumerate(tweet_cache.media_users.most_common(10)): 
                item, count = item_count
                print "{} | {:.2f} | {}".format(count, 100*count/total_urls, item)
                
            start = time.time()
        # global M
        # succ=False
        # M+=1
        # if 'media' in data['entities']:
            # for m in data['entities']['media']:
                # if not succ:
                    # N+=1
                    # succ=True
                    # print
                # #print N, M, "MEDIA", m['expanded_url']
                # print N, M, len(tweet_cache.media), "MEDIA", m['expanded_url']
        # if 'urls' in data['entities']:
            # for u in data['entities']['urls']:
                # if not succ:
                    # N+=1
                    # succ=True
                    # print
                # #print N, M, "URL", u['expanded_url']
                # print N, M, len(tweet_cache.urls), "URL", u['expanded_url']
                
    def on_error(self, status_code, data):
        print "[ON ERROR]", status_code

if __name__ == "__main__":
    #error_count = 0
    from collections import Counter
    exception_catcher = Counter()
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    #tweet_cache.register_datastore(tweets)
    while True:
        try:
            stream.statuses.filter(track=
                ['terrorists','attack','attacked','killed','hostage','hostages','explosion','bomb','bomber'])
            #stream.statuses.sample()
        except Exception, e:
            exception_catcher[e] +=1
            print "[ERROR]", e, exception_catcher[e]
            #raise e
    