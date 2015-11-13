from code.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from code.utilities import store_tweets, handle_rate_limiting
from twython import TwythonStreamer
from requests.exceptions import ChunkedEncodingError
from cache import TweetCache

# Looks like the TwythonStreamer class handles rate limiting for me!
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
        global N
        global M
        global tweet_cache
        tweet_cache.update(data)
        succ=False
        M+=1
        if 'media' in data['entities']:
            for m in data['entities']['media']:
                if not succ:
                    N+=1
                    succ=True
                    print
                #print N, M, "MEDIA", m['expanded_url']
                print N, M, len(tweet_cache.media), "MEDIA", m['expanded_url']
        if 'urls' in data['entities']:
            for u in data['entities']['urls']:
                if not succ:
                    N+=1
                    succ=True
                    print
                #print N, M, "URL", u['expanded_url']
                print N, M, len(tweet_cache.urls), "URL", u['expanded_url']
                
    def on_error(self, status_code, data):
        print status_code

if __name__ == "__main__":
    error_count = 0
    
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    stream.statuses.filter(track='Paris')
    # while True:
        # try:
            # stream.statuses.sample()
        # except ChunkedEncodingError:
            # error_count +=1
            # print "~~~~~~~~~~~~ ChunkedEncodingError ~~~~~~~~~~~~"
            # print error_count
            # print "~~~~~~~~~~~~ ChunkedEncodingError ~~~~~~~~~~~~"