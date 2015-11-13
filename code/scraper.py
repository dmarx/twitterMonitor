from code.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from code.utilities import store_tweets, handle_rate_limiting
from twython import TwythonStreamer

# Looks like the TwythonStreamer class handles rate limiting for me!
tweet_cache=[]
N=0
class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'limit' in data:
            return
        global N
        global tweet_cache
        tweet_cache.append(data)
        succ=False
        if 'media' in data['entities']:
            for m in data['entities']['media']:
                if not succ:
                    N+=1
                    succ=True
                    print
                print N, "MEDIA", m['expanded_url']
        if 'urls' in data['entities']:
            for u in data['entities']['urls']:
                if not succ:
                    N+=1
                    succ=True
                    print
                print N, "URL", u['expanded_url']
                
    def on_error(self, status_code, data):
        print status_code

if __name__ == "__main__":
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    #stream.statuses.filter(track='YesSheCan')
    stream.statuses.filter(track='the')
